"""
Webhook server for Telegram bot using Flask.
Receives updates from Telegram via webhook instead of polling.
"""

import os
import logging
from flask import Flask, request, jsonify
from telegram import Update
import json
from bot_handler import TelegramReferralBot

logger = logging.getLogger(__name__)

class WebhookServer:
    """Manages the webhook server for the Telegram bot."""
    
    def __init__(self, bot: TelegramReferralBot, port: int = 8000):
        """Initialize webhook server."""
        self.bot = bot
        self.port = port
        self.app = Flask(__name__)
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
                    # Process the update
                    self.bot.application.update_queue.put_nowait(update)
                    logger.debug(f"Received update: {update.update_id}")
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
            
            # Ensure webhook URL ends with token
            if not webhook_url.endswith('/'):
                webhook_url += '/'
            webhook_url += f'webhook/{self.bot.token}'
            
            logger.info(f"Setting up webhook at: {webhook_url}")
            
            await self.bot.application.bot.set_webhook(url=webhook_url)
            
            # Verify webhook was set
            webhook_info = await self.bot.application.bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}", exc_info=True)
            return False
    
    def run(self):
        """Run the webhook server."""
        port = int(os.getenv('PORT', self.port))
        host = '0.0.0.0'
        
        logger.info(f"Starting webhook server on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)
