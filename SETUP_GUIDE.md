# Telegram Referral Bot - Setup Guide

## Quick Start

Your Telegram referral bot is ready! Follow these simple steps to get it running:

### Step 1: Create Your Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "My Referral Bot")
4. Choose a username for your bot (e.g., "my_referral_bot")
5. Copy the bot token that BotFather gives you

### Step 2: Set Up Your Bot Token

In the left sidebar of this project, click on "Secrets" and add:
- **Key**: `TELEGRAM_BOT_TOKEN`
- **Value**: Your bot token from BotFather

Also add:
- **Key**: `BOT_USERNAME`
- **Value**: Your bot's username (without the @ symbol)

### Step 3: Start Your Bot

The bot will automatically restart once you add the secrets. You can see it running in the console on the right.

### Step 4: Set Up Your Channel

1. Add your bot to your Telegram channel as an administrator
2. Give it these permissions:
   - Invite users via link
   - Read messages
   - Send messages

### Step 5: Test Your Bot

1. Start a private chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Use `/admin` in your channel to see channel statistics

## How It Works

### For Channel Members:
1. **Join via referral**: Users click referral links to join your channel
2. **Get their link**: After joining, they receive their unique referral link
3. **Share and earn**: They share their link to invite 10 friends
4. **Claim rewards**: Once they reach 10 referrals, they can claim their reward

### For Channel Admins:
- Use `/admin` in your channel to see statistics
- Track total users, referrals, and rewards claimed
- Monitor channel growth through the referral system

## Bot Commands

**User Commands:**
- `/start` - Start the bot or join via referral link
- `/status` - Check referral progress  
- `/claim` - Claim available rewards
- `/help` - Show help message

**Admin Commands:**
- `/admin` - View channel statistics (channel admins only)

## Customization

You can customize these settings by adding them to your Secrets:

- `REFERRAL_TARGET` - How many referrals needed for reward (default: 10)
- `REWARD_TYPE` - Type of reward (default: "Premium Access")
- `ADMIN_IDS` - Comma-separated admin user IDs for special privileges

## Features

✅ **Multi-channel support** - Works with multiple channels simultaneously  
✅ **Real-time tracking** - Automatically tracks joins and leaves  
✅ **Progress monitoring** - Users can check their referral progress  
✅ **Reward system** - Automatic reward eligibility when targets are met  
✅ **Admin controls** - Channel statistics and management  
✅ **Data persistence** - All data is safely stored and backed up  

## Need Help?

If you need assistance:
1. Check the console logs on the right for any error messages
2. Make sure your bot token and username are correctly set in Secrets
3. Ensure your bot has admin permissions in your channel
4. Test with a small group first before promoting widely

Your referral system is ready to help grow your Telegram community!