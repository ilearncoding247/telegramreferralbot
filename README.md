# Telegram Referral Bot

A Python-based Telegram bot that creates and manages referral systems for Telegram channels with progress tracking and rewards.

## Features

- 🔗 **Referral Link Generation**: Creates unique referral links for each user and channel
- 📊 **Progress Tracking**: Tracks successful referrals and member activity
- 🎁 **Reward System**: Allows users to claim rewards after reaching referral targets
- 📈 **Real-time Updates**: Monitors channel joins and leaves automatically
- 🏆 **Multi-Channel Support**: Works with multiple channels simultaneously
- 💾 **Data Persistence**: Stores all data in JSON files for reliability
- 🔒 **Admin Controls**: Channel admin commands for statistics and management

## How It Works

1. **Bot Setup**: Add the bot as an admin to your Telegram channel
2. **User Onboarding**: Users start the bot and get invited to channels via referral links
3. **Referral Generation**: After joining, users receive their unique referral link
4. **Progress Tracking**: Bot tracks when people join/leave via referral links
5. **Reward Claims**: Users can claim rewards after reaching the referral target (default: 10 referrals)

## Installation

### Prerequisites

- Python 3.7+
- A Telegram bot token (get one from [@BotFather](https://t.me/botfather))

### Setup

1. **Clone or download the bot files**

2. **Install dependencies**:
   ```bash
   pip install python-telegram-bot
   ```

3. **Set up environment variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export BOT_USERNAME="your_bot_username"
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

## Configuration

Set these environment variables to customize the bot:

### Required
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `BOT_USERNAME`: Your bot's username (without @)

### Optional
- `REFERRAL_TARGET`: Number of referrals needed for reward (default: 10)
- `REWARD_TYPE`: Type of reward to give (default: "Premium Access")
- `ADMIN_IDS`: Comma-separated list of admin user IDs
- `LOG_LEVEL`: Logging level (default: INFO)

## Bot Commands

### User Commands
- `/start` - Start the bot or join via referral link
- `/status` - Check your referral progress
- `/claim` - Claim available rewards
- `/help` - Show help message

### Admin Commands (Channel admins only)
- `/admin` - View channel statistics and management options

## Setting Up Your Bot

1. **Create a Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command
   - Choose a name and username for your bot
   - Copy the bot token

2. **Configure the Bot**:
   - Set the bot token in your environment
   - Update the `BOT_USERNAME` in your environment
   - Customize referral targets and rewards as needed

3. **Add Bot to Channel**:
   - Add your bot as an administrator to your Telegram channel
   - Give it necessary permissions (at minimum: invite users, read messages)

4. **Start the Bot**:
   - Run `python main.py`
   - The bot will start and begin monitoring your channels

## File Structure

