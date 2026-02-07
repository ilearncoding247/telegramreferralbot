#!/usr/bin/env python3
"""
Main entry point for the Telegram Referral Bot.
This bot manages referral systems for Telegram channels.

Supports two modes:
- Polling mode (local development): python main.py
- Webhook mode (production on Render): python main.py webhook
"""

import os
import sys
import logging
import asyncio
from bot_handler import TelegramReferralBot

# Load environment variables (optional in prod, vital in dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_webhook_mode(bot):
    """Start bot in webhook mode (for production)."""
    from webhook_server import WebhookServer
    
    webhook_server = WebhookServer(bot)
    
    # Setup webhook with Telegram
    success = await webhook_server.setup_webhook()
    if not success:
        logger.error("Failed to setup webhook!")
        return False
    
    logger.info("Webhook mode started. Bot is listening for updates...")
    
    # Start the Flask server (blocking)
    webhook_server.run()

def start_polling_mode(bot):
    """Start bot in polling mode (for local development)."""
    logger.info("Starting bot in polling mode...")
    bot.start()

def main():
    """Main function to start the Telegram bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please set your bot token: export TELEGRAM_BOT_TOKEN='your_token_here'")
        return
    
    # Initialize the bot
    try:
        bot = TelegramReferralBot(bot_token)
        
        # Check if webhook mode is requested
        webhook_mode = os.getenv('WEBHOOK_MODE', 'false').lower() == 'true'
        
        # Also check command line arguments
        if len(sys.argv) > 1 and sys.argv[1].lower() == 'webhook':
            webhook_mode = True
        
        if webhook_mode:
            logger.info("Mode: Webhook (Production)")
            # Run webhook mode
            asyncio.run(start_webhook_mode(bot))
        else:
            logger.info("Mode: Polling (Development)")
            # Run polling mode
            start_polling_mode(bot)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
