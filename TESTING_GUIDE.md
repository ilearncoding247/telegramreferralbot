# Testing Your Telegram Referral Bot

Your bot is now live and ready for testing! Here's how to test each feature:

## 1. Basic Bot Testing

**Test the bot directly:**
1. Open Telegram and search for your bot by username
2. Start a chat and send `/start`
3. You should see a welcome message with inline buttons
4. Try `/help` to see all available commands
5. Try `/status` to check your referral progress

## 2. Channel Setup Testing

**Add bot to your channel:**
1. Go to your Telegram channel
2. Add your bot as an administrator
3. Give it these permissions:
   - Invite users via link
   - Read messages
   - Send messages
   - Manage chat

**Test admin features:**
1. In your channel, send `/admin`
2. You should see channel statistics
3. The bot will register your channel automatically

## 3. Referral System Testing

**Test the referral flow:**
1. Create a test channel or use an existing one
2. Add your bot as admin to the channel
3. Have a friend (or second account) message your bot with `/start`
4. Add that person to your channel
5. They should receive a referral link automatically
6. Have them share that link and test the referral process

## 4. Reward System Testing

**Test reward claiming:**
1. Manually test with multiple accounts joining via referral links
2. Once someone reaches 10 referrals, they can use `/claim`
3. Test the reward claiming process

## 5. Expected Bot Behavior

### When users start the bot:
- Welcome message with inline buttons
- Help and status options available

### When users join a channel:
- Bot automatically sends them a personalized referral link
- Progress tracking begins

### When someone uses a referral link:
- Bot tracks the referral
- Referrer gets notified of successful referral
- Progress is updated automatically

### When users check status:
- Shows progress for each channel
- Displays referrals needed to reach target
- Shows available rewards

### When users claim rewards:
- Lists available rewards by channel
- Processes reward claims
- Updates reward count

## 6. Data Storage

Your bot automatically creates a `data/` folder with:
- `users.json` - User data and progress
- `channels.json` - Channel information
- `referrals.json` - Referral code mappings
- `pending.json` - Pending referral joins

## 7. Troubleshooting

**If the bot doesn't respond:**
- Check that it's added as admin to your channel
- Verify the bot has proper permissions
- Check the console logs for errors

**If referrals aren't tracked:**
- Ensure users are joining via the referral links
- Check that the bot can see chat member updates
- Verify channel permissions are correct

**If you need to reset data:**
- Delete the `data/` folder to start fresh
- The bot will recreate it automatically

Your referral system is now ready to help grow your Telegram community!