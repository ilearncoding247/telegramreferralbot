# Deploying to Render with Webhook Mode

This guide explains how to deploy the Telegram Referral Bot to Render using webhook mode (recommended for production).

## What's Changed?

The bot now supports **webhook mode** instead of just polling. This means:
- ✅ Bot receives updates from Telegram via webhook (not polling)
- ✅ No more deployment timeouts on Render
- ✅ More efficient and scalable
- ✅ Binds to port required by Render

## Prerequisites

1. A Telegram bot created via [@BotFather](https://t.me/botfather)
2. A Render account (free tier works)
3. Your repository pushed to GitHub

## Step-by-Step Deployment to Render

### Step 1: Create a Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Fill in the details:
   - **Name**: `telegram-referral-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py webhook`
   - **Instance Type**: Free (fine for testing)

### Step 2: Add Environment Variables

In the Render dashboard, go to **Environment** and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username
WEBHOOK_URL=https://your-service-name.onrender.com
```

**Important**: Replace these values:
- `your_bot_token_here` - Get from [@BotFather](https://t.me/botfather)
- `your_bot_username` - Your bot's username without the @
- `your-service-name` - Your Render service name (from Step 1)

### Step 3: Deploy

1. Click **Create Web Service**
2. Render will automatically deploy your bot
3. Wait for the build to complete (2-3 minutes)
4. Check the logs to confirm it started successfully

You should see logs like:
```
Setting up webhook at: https://your-service-name.onrender.com/webhook/YOUR_TOKEN
Bot is listening for updates...
```

### Step 4: Verify the Deployment

1. Open `https://your-service-name.onrender.com/health` in your browser
2. You should see: `{"status":"ok"}`
3. Test your bot on Telegram by sending `/start`

## Environment Variables Explained

| Variable | Required | Example |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `BOT_USERNAME` | Yes | `my_referral_bot` |
| `WEBHOOK_URL` | Yes | `https://telegram-referral-bot.onrender.com` |
| `WEBHOOK_MODE` | No | `true` (set by start command) |

## How Webhook Mode Works

```
Telegram Server
     ↓ (sends update)
Render Web Service (webhook_server.py)
     ↓ (converts to Update object)
bot_handler.py (processes command)
     ↓ (calls handlers)
Your bot logic
```

**vs. Old Polling Mode (deleted):**
```
Your Bot
  ↓ (asks Telegram)
Telegram: "Any messages for me?"
  ↓ (polling interval: asks every ~1 sec)
```

Webhook mode is faster and more efficient!

## Troubleshooting

### "Timed out waiting for available port"
- This was the original issue! Webhook mode fixes it.
- Make sure `WEBHOOK_URL` is set correctly
- Check that the service type is **Web Service** (not Background Worker)

### "Bot not responding to messages"
- Check the logs in Render dashboard
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Make sure `WEBHOOK_URL` doesn't have a trailing slash

### "Webhook setup failed"
- Ensure `WEBHOOK_URL` is exactly: `https://your-service-name.onrender.com`
- No trailing slash!
- Service must be running and accessible

### Health check endpoint working but bot not updating
- Check that Telegram can reach your webhook
- Try: `curl https://your-service-name.onrender.com/health`
- If it works, the issue might be in bot token or webhook URL

## Local Development

To test locally **without** webhook mode, use polling:

```bash
export TELEGRAM_BOT_TOKEN=your_token
export BOT_USERNAME=your_username
python main.py
```

This runs in polling mode (the bot asks Telegram for messages).

To test webhook mode locally:

```bash
export TELEGRAM_BOT_TOKEN=your_token
export BOT_USERNAME=your_username
export WEBHOOK_URL=http://localhost:5000
python main.py webhook
```

## Switching Back to Polling (Not Recommended)

If you want to use polling instead:

1. Change Procfile: `web: python main.py`
2. Delete the `WEBHOOK_MODE` variable
3. Deploy again

⚠️ Render will likely timeout again, so webhook is strongly recommended.

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [python-telegram-bot Webhook Documentation](https://docs.python-telegram-bot.org/)
- [BotFather Commands](https://core.telegram.org/bots#botfather)

## Support

If you encounter issues:
1. Check Render logs for error messages
2. Verify all environment variables are set
3. Test the bot locally first with polling mode
4. Ensure your bot has proper permissions in your channel

Happy deploying! 🚀
