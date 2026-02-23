"""
Centralized message and button label management for the Telegram Referral Bot.
Edit this file to customize the bot's personality and language.
"""

class BotMessages:
    # --- BUTTON LABELS ---
    BTN_CREATE_LINK = "🔗 Create Link / View Link"
    BTN_MY_LINK = "💎 My Link"
    BTN_STATUS = "📊 Status"
    BTN_GET_REWARD = "🎁 Get Reward"
    BTN_HELP = "❓ Help"
    BTN_BACK_MENU = "🔙 Back to Menu"
    BTN_REFRESH = "🔄 Refresh"
    BTN_CHANNEL_GET_LINK = "Get my referral link"

    # --- MAIN BOT MESSAGES ---
    
    # Sent when a user joins or uses /start
    WELCOME_PRIVATE = (
        "🎉 Welcome to EarnPro, {first_name}!\n\n"
        "Your journey to building a network starts here. 🌐\n\n"
        "🔗 *Here is your unique referral link:*\n"
        "`{referral_link}`\n\n"
        "1. Copy this link.\n"
        "2. Share it with your friends.\n"
        "3. When they join the channel, you get credit!\n\n"
        "🎯 Goal: Invite {target} friends to earn rewards.\n"
        "#YourReferralsYourNetwork"
    )

    # Sent to a user in the channel if the bot can't DM them
    WELCOME_CHANNEL_FALLBACK = (
        "Welcome to EarnPro, @{user_name}! 🚀\n"
        "Your journey to building a network starts here. 🌐\n"
        "Tap 'Get my referral link' below to start the bot and claim your unique link.\n"
        "#YourReferralsYourNetwork"
    )

    # Help command text
    HELP_TEXT = (
        "🤖 *Referral Bot Commands*\n\n"
        "• `/start` - **Create/View Link**: Generates your unique referral link.\n"
        "• `/status` - **Check Status**: Shows how many users have joined via your link.\n"
        "• `/mylink` - **My Link**: Shows your unique referral link.\n"
        "• `/claim` - **Get Reward**: If you have referrals, tells you how to redeem.\n"
        "• `/help` - **Help**: Shows this explanation.\n\n"
        "*How to Earn:*\n"
        "1️⃣ Get your link with /start\n"
        "2️⃣ Invite {target} friends to the Channel\n"
        "3️⃣ Use /claim to get redemption instructions!"
    )

    # Status response
    STATUS_HEADER = "📊 *Your Referral Status*\n\n"
    STATUS_CHANNEL_LINE = "🔸 *{channel_name}*\n"
    STATUS_DETAILS = (
        "   • Referrals: {count}/{target}\n"
        "   • Progress: {progress_bar}\n"
        "   • Rewards claimed: {claimed}\n"
    )
    STATUS_READY_TO_CLAIM = "   • ✅ Ready to claim reward!\n"
    STATUS_NEED_MORE = "   • 🎯 Need {rem} more referrals\n"
    STATUS_EMPTY = (
        "📊 *Your Referral Status*\n\n"
        "You haven't joined any channels yet.\n"
        "Use a referral link to get started!"
    )

    # Reward claim - Eligible
    CLAIM_ELIGIBLE = (
        "🏆 *Congratulations! You are eligible for rewards!* 🏆\n\n"
        "You have referred {count} people.\n\n"
        "👇 **HOW TO REDEEM:**\n"
        "1. Log into your [EarnPro Dashboard](https://earnpro.org/dashboard).\n"
        "2. Go to the 'Rewards' section.\n"
        "3. Enter your Telegram Username or ID to verify.\n\n"
        "Your Telegram ID: `{user_id}`"
    )

    # Reward claim - Not Eligible
    CLAIM_LOCKED = (
        "🔒 *Rewards Locked*\n\n"
        "You have referred {count} people.\n"
        "You need **{target} referrals** to unlock rewards.\n\n"
        "Keep inviting! You only need {rem} more!"
    )

    # Notification to the person who invited someone
    REFERRAL_NOTIFICATION = (
        "🚀 *New Referral!*\n\n"
        "Hi! {new_member} just joined using your link!\n"
        "📊 Total Referrals: {count}/{target}\n"
    )
    
    REFERRAL_MILESTONE_REACHED = (
        "\n🏆 *TARGET REACHED!* 🏆\n"
        "You have reached {target} referrals!\n"
        "Use /claim to get your reward instructions."
    )

    # My Link command
    MY_LINK_MESSAGE = (
        "🔗 *Your Unique Referral Link:*\n\n"
        "`{referral_link}`\n\n"
        "Tap to copy and share!"
    )
    MY_LINK_MISSING = (
        "⚠️ You don't have a referral link yet.\n"
        "Use /start to generate one!"
    )
