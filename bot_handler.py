"""
Telegram Bot Handler for managing referral systems.
Handles all bot commands and user interactions.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from referral_manager import ReferralManager
from data_manager import DataManager
from config import Config
import utils

logger = logging.getLogger(__name__)

class TelegramReferralBot:
    """Main bot class that handles all Telegram interactions."""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.referral_manager = ReferralManager()
        self.data_manager = DataManager()
        self.config = Config()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up all command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("claim", self.claim_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Chat member handler for tracking joins/leaves
        self.application.add_handler(ChatMemberHandler(self.track_chat_member, ChatMemberHandler.CHAT_MEMBER))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for processing referral links
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context):
        """Handle /start command."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Check if this is a referral link
        if context.args:
            referral_code = context.args[0]
            await self._handle_referral_join(update, referral_code)
            return
        
        # Regular start command
        if chat.type == 'private':
            # Check for pending welcome messages
            user_data = self.data_manager.get_user_data(user.id)
            pending_messages = []
            
            if user_data and user_data.get('channels'):
                for channel_id, channel_data in user_data['channels'].items():
                    if channel_data.get('pending_welcome'):
                        channel_info = self.data_manager.get_channel_info(channel_id)
                        channel_name = channel_info.get('name', 'Unknown Channel') if channel_info else 'Unknown Channel'
                        referral_link = channel_data.get('referral_link', '')
                        
                        if referral_link:
                            pending_message = (
                                f"🎉 Welcome to {channel_name}!\n\n"
                                f"🔗 Here's your unique referral link:\n"
                                f"`{referral_link}`\n\n"
                                f"Share this link to invite {self.config.REFERRAL_TARGET} friends "
                                f"and earn rewards!\n\n"
                            )
                            pending_messages.append(pending_message)
                            
                            # Mark as sent
                            channel_data['pending_welcome'] = False
                            self.data_manager.save_user_data(user.id, user_data)
            
            # Send pending messages first
            for msg in pending_messages:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
            # Send main welcome message
            welcome_message = (
                f"🎉 Welcome to the Referral Bot, {user.first_name}!\n\n"
                "I help you manage referral systems for Telegram channels.\n\n"
                "🔹 Get invited to channels and earn rewards\n"
                "🔹 Share your referral links to invite others\n"
                "🔹 Track your progress and claim rewards\n\n"
                "Use /help to see all available commands."
            )
            
            keyboard = [
                [InlineKeyboardButton("📊 My Status", callback_data="status")],
                [InlineKeyboardButton("🎁 Claim Rewards", callback_data="claim")],
                [InlineKeyboardButton("❓ Help", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                "👋 Hi! I'm a referral bot. Add me as an admin to your channel to start using referral features!"
            )
    
    async def help_command(self, update: Update, context):
        """Handle /help command."""
        help_text = (
            "🤖 *Referral Bot Help*\n\n"
            "*Available Commands:*\n"
            "• `/start` - Start the bot or join via referral link\n"
            "• `/status` - Check your referral progress\n"
            "• `/claim` - Claim your rewards\n"
            "• `/help` - Show this help message\n"
            "• `/admin` - Admin commands (channel admins only)\n\n"
            "*How it works:*\n"
            "1️⃣ Join a channel via referral link\n"
            "2️⃣ Get your unique referral link\n"
            "3️⃣ Share it to invite others\n"
            "4️⃣ Earn rewards when people join!\n\n"
            "*Need help?* Contact the channel admin."
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context):
        """Handle /status command."""
        user_id = update.effective_user.id
        user_data = self.data_manager.get_user_data(user_id)
        
        if not user_data or not user_data.get('channels'):
            await update.message.reply_text(
                "📊 *Your Referral Status*\n\n"
                "You haven't joined any channels yet.\n"
                "Use a referral link to get started!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        status_text = "📊 *Your Referral Status*\n\n"
        
        for channel_id, channel_data in user_data['channels'].items():
            channel_info = self.data_manager.get_channel_info(channel_id)
            channel_name = channel_info.get('name', 'Unknown Channel') if channel_info else 'Unknown Channel'
            
            successful_referrals = channel_data.get('successful_referrals', 0)
            target = self.config.REFERRAL_TARGET
            rewards_claimed = channel_data.get('rewards_claimed', 0)
            
            status_text += f"🔸 *{channel_name}*\n"
            status_text += f"   • Referrals: {successful_referrals}/{target}\n"
            status_text += f"   • Progress: {utils.get_progress_bar(successful_referrals, target)}\n"
            status_text += f"   • Rewards claimed: {rewards_claimed}\n"
            
            if successful_referrals >= target:
                status_text += "   • ✅ Ready to claim reward!\n"
            else:
                remaining = target - successful_referrals
                status_text += f"   • 🎯 Need {remaining} more referrals\n"
            
            status_text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🎁 Claim Rewards", callback_data="claim")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def claim_command(self, update: Update, context):
        """Handle /claim command."""
        user_id = update.effective_user.id
        user_data = self.data_manager.get_user_data(user_id)
        
        if not user_data or not user_data.get('channels'):
            await update.message.reply_text(
                "🎁 *Claim Rewards*\n\n"
                "You haven't joined any channels yet.\n"
                "Use a referral link to get started!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        claimable_rewards = []
        
        for channel_id, channel_data in user_data['channels'].items():
            successful_referrals = channel_data.get('successful_referrals', 0)
            rewards_claimed = channel_data.get('rewards_claimed', 0)
            
            if successful_referrals >= self.config.REFERRAL_TARGET:
                available_rewards = successful_referrals // self.config.REFERRAL_TARGET - rewards_claimed
                if available_rewards > 0:
                    channel_info = self.data_manager.get_channel_info(channel_id)
                    channel_name = channel_info.get('name', 'Unknown Channel') if channel_info else 'Unknown Channel'
                    claimable_rewards.append((channel_id, channel_name, available_rewards))
        
        if not claimable_rewards:
            await update.message.reply_text(
                "🎁 *Claim Rewards*\n\n"
                "No rewards available to claim.\n"
                "Keep inviting friends to earn rewards!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Create claim buttons
        keyboard = []
        for channel_id, channel_name, available_rewards in claimable_rewards:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎁 Claim {available_rewards} reward(s) - {channel_name}",
                    callback_data=f"claim_{channel_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        claim_text = "🎁 *Available Rewards*\n\n"
        for _, channel_name, available_rewards in claimable_rewards:
            claim_text += f"🔸 {channel_name}: {available_rewards} reward(s)\n"
        
        claim_text += "\nClick below to claim your rewards!"
        
        await update.message.reply_text(claim_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def admin_command(self, update: Update, context):
        """Handle /admin command for channel administrators."""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type == 'private':
            await update.message.reply_text(
                "❌ Admin commands can only be used in channels where you're an admin."
            )
            return
        
        # Check if user is admin
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ You need to be a channel admin to use this command.")
            return
        
        # Register or update channel
        self.data_manager.register_channel(chat.id, chat.title or "Unknown Channel")
        
        channel_stats = self.referral_manager.get_channel_stats(chat.id)
        
        admin_text = (
            f"🔧 *Channel Admin Panel*\n\n"
            f"📊 *Channel Statistics:*\n"
            f"• Total users: {channel_stats.get('total_users', 0)}\n"
            f"• Active referrers: {channel_stats.get('active_referrers', 0)}\n"
            f"• Total referrals: {channel_stats.get('total_referrals', 0)}\n"
            f"• Rewards claimed: {channel_stats.get('rewards_claimed', 0)}\n\n"
            f"🎯 *Settings:*\n"
            f"• Referral target: {self.config.REFERRAL_TARGET}\n"
            f"• Reward type: {self.config.REWARD_TYPE}\n"
        )
        
        await update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)
    
    async def track_chat_member(self, update: Update, context):
        """Track when users join or leave channels."""
        chat_member_update = update.chat_member
        chat = update.effective_chat
        user = chat_member_update.new_chat_member.user
        
        # Skip bot updates
        if user.is_bot:
            return
        
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status
        
        # User joined the channel
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
            await self._handle_user_join(chat.id, user.id, user.first_name)
        
        # User left the channel
        elif old_status in ['member', 'administrator', 'creator'] and new_status in ['left', 'kicked']:
            await self._handle_user_leave(chat.id, user.id)
    
    async def _handle_user_join(self, chat_id: int, user_id: int, user_name: str):
        """Handle when a user joins a channel."""
        logger.info(f"User {user_id} joined channel {chat_id}")
        
        # Check if this was a referral join
        pending_referral = self.data_manager.get_pending_referral(user_id, chat_id)
        
        if pending_referral:
            # This was a referral join
            referrer_id = pending_referral['referrer_id']
            self.referral_manager.process_successful_referral(referrer_id, chat_id, user_id)
            self.data_manager.remove_pending_referral(user_id, chat_id)
            
            # Notify referrer
            try:
                await self.application.bot.send_message(
                    referrer_id,
                    f"🎉 Great! Someone joined via your referral link!\n\n"
                    f"Use /status to check your progress."
                )
            except Exception as e:
                logger.error(f"Failed to notify referrer {referrer_id}: {e}")
        
        # Generate referral link for the new user
        referral_link = self.referral_manager.generate_referral_link(user_id, chat_id)
        
        # Send welcome message with referral link
        try:
            welcome_message = (
                f"🎉 Welcome to the channel!\n\n"
                f"🔗 Here's your unique referral link:\n"
                f"`{referral_link}`\n\n"
                f"Share this link to invite {self.config.REFERRAL_TARGET} friends "
                f"and earn rewards!\n\n"
                f"Use /status to track your progress."
            )
            
            await self.application.bot.send_message(
                user_id,
                welcome_message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Could not send welcome message to user {user_id} - they need to start the bot first: {e}")
            # Store the referral link to send later when they start the bot
            user_data = self.data_manager.get_user_data(user_id) or {'channels': {}}
            channel_key = str(chat_id)
            if channel_key not in user_data['channels']:
                user_data['channels'][channel_key] = {}
            user_data['channels'][channel_key]['pending_welcome'] = True
            user_data['channels'][channel_key]['referral_link'] = referral_link
            self.data_manager.save_user_data(user_id, user_data)
    
    async def _handle_user_leave(self, chat_id: int, user_id: int):
        """Handle when a user leaves a channel."""
        logger.info(f"User {user_id} left channel {chat_id}")
        
        # Find who referred this user and decrement their count
        referrer_id = self.referral_manager.find_referrer(chat_id, user_id)
        if referrer_id:
            self.referral_manager.process_referral_leave(referrer_id, chat_id, user_id)
            
            # Notify referrer
            try:
                await self.application.bot.send_message(
                    referrer_id,
                    f"😔 Someone you referred has left the channel.\n\n"
                    f"Use /status to check your updated progress."
                )
            except Exception as e:
                logger.error(f"Failed to notify referrer {referrer_id}: {e}")
    
    async def _handle_referral_join(self, update: Update, referral_code: str):
        """Handle when someone joins via a referral link."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Decode referral code
        referral_data = utils.decode_referral_code(referral_code)
        if not referral_data:
            await update.message.reply_text(
                "❌ Invalid referral link. Please check the link and try again."
            )
            return
        
        referrer_id = referral_data['referrer_id']
        channel_id = referral_data['channel_id']
        
        # Check if user is trying to refer themselves
        if referrer_id == user_id:
            await update.message.reply_text(
                "❌ You cannot use your own referral link!"
            )
            return
        
        # Check if user is already in the channel
        try:
            chat_member = await self.application.bot.get_chat_member(channel_id, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                await update.message.reply_text(
                    "ℹ️ You're already a member of this channel!"
                )
                return
        except Exception:
            pass  # User not in channel, continue
        
        # Store pending referral
        self.data_manager.add_pending_referral(user_id, channel_id, referrer_id)
        
        # Get channel info
        try:
            chat = await self.application.bot.get_chat(channel_id)
            channel_name = chat.title
            
            # Create invite link
            invite_link = await self.application.bot.create_chat_invite_link(channel_id)
            
            join_message = (
                f"🎉 Welcome! You've been invited to join:\n\n"
                f"📺 *{channel_name}*\n\n"
                f"Click the link below to join:\n"
                f"{invite_link.invite_link}\n\n"
                f"After joining, you'll get your own referral link to earn rewards!"
            )
            
            await update.message.reply_text(join_message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Failed to process referral join: {e}")
            await update.message.reply_text(
                "❌ There was an error processing your referral. "
                "Please make sure the bot is added as an admin to the channel."
            )
    
    async def handle_callback(self, update: Update, context):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "status":
            await self.status_command(update, context)
        elif query.data == "claim":
            await self.claim_command(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data.startswith("claim_"):
            channel_id = int(query.data.split("_")[1])
            await self._process_reward_claim(update, channel_id)
    
    async def _process_reward_claim(self, update: Update, channel_id: int):
        """Process a reward claim."""
        user_id = update.effective_user.id
        
        # Validate and process claim
        result = self.referral_manager.claim_reward(user_id, channel_id)
        
        if result['success']:
            channel_info = self.data_manager.get_channel_info(channel_id)
            channel_name = channel_info.get('name', 'Unknown Channel') if channel_info else 'Unknown Channel'
            
            success_message = (
                f"🎉 *Congratulations!*\n\n"
                f"You've successfully claimed your reward for {channel_name}!\n\n"
                f"🎁 Reward: {self.config.REWARD_TYPE}\n"
                f"📊 Total rewards claimed: {result['total_claimed']}\n\n"
                f"Keep inviting friends to earn more rewards!"
            )
            
            await update.callback_query.edit_message_text(
                success_message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.callback_query.edit_message_text(
                f"❌ {result['message']}"
            )
    
    async def handle_message(self, update: Update, context):
        """Handle regular text messages."""
        # For now, just acknowledge the message
        # This could be expanded to handle other interactions
        pass
    
    def start(self):
        """Start the bot."""
        logger.info("Bot is starting...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def stop(self):
        """Stop the bot."""
        logger.info("Bot is stopping...")
        self.application.stop()
