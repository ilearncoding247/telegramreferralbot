"""
Webhook server for Telegram bot using Flask.
Receives updates from Telegram via webhook instead of polling.
"""

import os
import logging
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update, Bot
from bot_handler import TelegramReferralBot

logger = logging.getLogger(__name__)

class WebhookServer:
    """Manages the webhook server for the Telegram bot."""
    
    def __init__(self, bot: TelegramReferralBot, port: int = 8000):
        """Initialize webhook server."""
        self.bot = bot
        self.port = port
        self.app = Flask(__name__)
        self.loop = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint for deployment services."""
            return jsonify({'status': 'ok'}), 200
        
        @self.app.route(f'/webhook/{self.bot.token}', methods=['POST'])
        def webhook():
            """Webhook endpoint to receive Telegram updates."""
            try:
                data = request.get_json()
                
                if not data:
                    logger.warning("Received empty webhook data")
                    return jsonify({'ok': False, 'message': 'No data'}), 400
                
                # Convert to Telegram Update object
                update = Update.de_json(data, self.bot.application.bot)
                
                if update:
                    logger.debug(f"Received update: {update.update_id}")
                    # Schedule the update to be processed by the application
                    if self.loop:
                        asyncio.run_coroutine_threadsafe(
                            self.bot.application.process_update(update),
                            self.loop
                        )
                    return jsonify({'ok': True}), 200
                else:
                    logger.warning("Failed to parse update")
                    return jsonify({'ok': False, 'message': 'Invalid update'}), 400
                    
            except Exception as e:
                logger.error(f"Webhook error: {e}", exc_info=True)
                return jsonify({'ok': False, 'error': str(e)}), 500
        
        @self.app.route('/', methods=['GET'])
        def index():
            """Index page."""
            return jsonify({'status': 'Bot is running', 'version': '1.0'}), 200
    
    async def setup_webhook(self):
        """Register the webhook with Telegram."""
        try:
            webhook_url = os.getenv('WEBHOOK_URL')
            if not webhook_url:
                logger.error("WEBHOOK_URL environment variable not set!")
                raise ValueError("WEBHOOK_URL not configured")
            
            # Ensure webhook URL ends properly
            if webhook_url.endswith('/'):
                webhook_url = webhook_url[:-1]
            webhook_url += f'/webhook/{self.bot.token}'
            
            logger.info(f"Setting up webhook at: {webhook_url}")
            
            # Set webhook
            await self.bot.application.bot.set_webhook(url=webhook_url)
            
            # Verify webhook was set
            webhook_info = await self.bot.application.bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}", exc_info=True)
            return False
    
    async def run_async(self):
        """Run the application and webhook server asynchronously."""
        # Initialize the application
        await self.bot.application.initialize()
        await self.bot.application.post_init(self.bot.application)
        
        # Setup webhook
        success = await self.setup_webhook()
        if not success:
            logger.error("Failed to setup webhook!")
            return False
        
        logger.info("Application initialized and webhook configured")
        return True
    
    def _run_app_loop(self):
        """Run the Flask app in a separate thread with its own event loop."""
        # Create a new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Run the Flask app
        port = int(os.getenv('PORT', self.port))
        host = '0.0.0.0'
        logger.info(f"Starting webhook server on {host}:{port}")
        self.app.run(host=host, port=port, debug=False, use_reloader=False)
    
    def run(self):
        """Run the webhook server and application."""
        # Initialize the application synchronously from the main event loop
        async def init():
            await self.bot.application.initialize()
            await self.bot.application.post_init(self.bot.application)
            success = await self.setup_webhook()
            if not success:
                logger.error("Failed to setup webhook!")
                return False
            logger.info("Webhook mode started. Bot is listening for updates...")
            return True
        
        # Run initialization
        try:
            # Create a new event loop for initialization
            init_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(init_loop)
            result = init_loop.run_until_complete(init())
            init_loop.close()
            
            if not result:
                return 1
        except Exception as e:
            logger.error(f"Failed to initialize: {e}", exc_info=True)
            return 1
        
        # Create a separate thread for the Flask app
        port = int(os.getenv('PORT', self.port))
        host = '0.0.0.0'
        logger.info(f"Starting webhook server on {host}:{port}")
        
        # Create event loop for processing updates
        self.loop = asyncio.new_event_loop()
        
        # Start Flask in main thread
        try:
            self.app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}", exc_info=True)
            return 1
        
        return 0

            return False
    

