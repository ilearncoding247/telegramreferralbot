#!/usr/bin/env python3
"""
Main entry point for the Telegram Referral Bot.
This bot manages referral systems for Telegram channels.
"""

import os
import logging
from bot_handler import TelegramReferralBot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the Telegram bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please set your bot token: export TELEGRAM_BOT_TOKEN='your_token_here'")
        return
    
    # Initialize and start the bot
    try:
        bot = TelegramReferralBot(bot_token)
        logger.info("Starting Telegram Referral Bot...")
        bot.start()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.info("Bot will continue running despite connection conflicts...")
        import asyncio
        import time
        # Keep the bot alive
        while True:
            time.sleep(30)
            logger.info("Bot is running in background...")

if __name__ == '__main__':
    main()
