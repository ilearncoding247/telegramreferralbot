"""
Telegram Bot Handler for managing referral systems.
Handles all bot commands and user interactions.
"""

import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode
from referral_manager import ReferralManager
from supabase_manager import SupabaseManager
from config import Config
from messages import BotMessages
import utils

logger = logging.getLogger(__name__)

class TelegramReferralBot:
    """Main bot class that handles all Telegram interactions."""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.application = Application.builder().token(token).post_init(self.post_init).build()
        self.config = Config()
        
        # Initialize Supabase Manager instead of DataManager
        self.data_manager = SupabaseManager(self.config)
        
        # Inject dependency
        self.referral_manager = ReferralManager(data_manager=self.data_manager)
        
        self._setup_handlers()

    async def post_init(self, application: Application):
        """Post-initialization hook."""
        # clear existing commands to force button usage
        await application.bot.delete_my_commands()
        logger.info("Cleared bot commands to enforce button usage.")
    
    def _setup_handlers(self):
        """Set up all command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("claim", self.claim_command))
        self.application.add_handler(CommandHandler("mylink", self.mylink_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        self.application.add_handler(CommandHandler("check", self.check_command))
        
        # Handle metrics and tracking
        self.application.add_handler(ChatMemberHandler(self.track_chat_member, ChatMemberHandler.CHAT_MEMBER))
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Fallback handler for dynamic channel commands (e.g. /MyChannelName)
        # We capture text messages starting with '/' that aren't other commands
        self.application.add_handler(MessageHandler(filters.COMMAND, self.dynamic_channel_command))

    async def dynamic_channel_command(self, update: Update, context):
        """Handle dynamic commands that match channel names."""
        command = update.message.text.split()[0][1:] # Remove leading '/'
        normalized_cmd = command.lower().replace(" ", "")
        
        # Search for matching channel
        all_channels = self.data_manager.get_all_channels()
        target_channel_id = None
        target_channel_name = None
        
        for c_id, c_data in all_channels.items():
            c_name = c_data.get('name', '')
            # Normalize channel name: remove spaces, lowercase
            normalized_name = c_name.lower().replace(" ", "")
            
            if normalized_name == normalized_cmd:
                target_channel_id = int(c_id)
                target_channel_name = c_name
                break
        
        if target_channel_id:
            # Found a matching channel! Show stats.
            await self._show_detailed_channel_stats(update, target_channel_id, target_channel_name)
        else:
            # Unknown command
            # Since this catches ALL unknown commands, we should be careful.
            # But the user asked for this.
            pass # Silent ignore or generic help? Silent is safer to avoid spam.

    async def _show_detailed_channel_stats(self, update: Update, channel_id: int, channel_name: str):
        """Show detailed stats for a specific channel (used by dynamic command)."""
        # Security: Only allow admins to check ANY channel? 
        # Or normal users to check THEIR status?
        # Context suggests User wants to check the EarnPro channel stats.
        # Assuming they want THEIR stats in that channel, OR overall admin stats if they are admin?
        # User request: manual channel status command -> likely implied "Status for this channel".
        
        user_id = update.effective_user.id
        
        # Check permissions - is user an admin of that channel? 
        # Hard to check remotely without querying TG API which requires user to be in chat.
        # Let's assume this is for "My Status in Channel X" unless Super Admin.
        
        is_super_admin = (user_id == self.config.SUPER_ADMIN_ID)
        
        if is_super_admin:
            # Show Admin Stats
            channel_stats = self.referral_manager.get_channel_stats(channel_id)
            text = (
                f"🔧 *Channel Stats: {channel_name}*\n\n"
                f"👥 Total Users: {channel_stats.get('total_users', 0)}\n"
                f"🗣️ Active Referrers: {channel_stats.get('active_referrers', 0)}\n"
                f"🔗 Total Referrals: {channel_stats.get('total_referrals', 0)}\n"
            )
        else:
            # Show User Stats
            progress = self.referral_manager.get_user_progress(user_id, channel_id)
            if not progress:
                text = f"📊 You have no data for *{channel_name}*."
            else:
                refs = progress.get('successful_referrals', 0)
                target = self.config.REFERRAL_TARGET
                text = (
                    f"📊 *Your Status in {channel_name}*\n\n"
                    f"👥 Referrals: {refs}/{target}\n"
                    f"🎁 Rewards: {progress.get('rewards_claimed', 0)}\n"
                )
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def check_command(self, update: Update, context):
        """Debug command to check invite links."""
        user = update.effective_user
        
        # Load mappings
        try:
            import json
            import os
            mapping_file = "data/invite_links.json"
            if not os.path.exists(mapping_file):
                await update.message.reply_text("❌ No invite links found.")
                return
                
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
        except Exception as e:
            await update.message.reply_text(f"❌ Error loading data: {e}")
            return

        # Find user's links
        user_links = []
        for link, data in mappings.items():
            if data.get('user_id') == user.id:
                user_links.append(link)
        
        if not user_links:
            await update.message.reply_text("⚠️ You have no tracked invite links in the database.")
            return
            
        message = f"🔍 *Found {len(user_links)} links for you:*\n\n"
        for link in user_links:
            # We can't easily get the 'joined count' from Telegram API directly for a link without being the creator/admin 
            # and using sensitive methods. 
            # But we can show what we know.
            message += f"🔗 `{link}`\n"
            message += f"   Select this link to copy it.\n"
            
        message += "\nℹ️ If you invite someone and the count doesn't go up, make sure they are joining via this exact link."
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    async def start_command(self, update: Update, context):
        """Handle /start command."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Check if this is a referral link or a deep link
        if context.args:
            arg = context.args[0]
            
            # Handle "getlink_" deep link from the group button
            if arg.startswith('getlink_'):
                try:
                    channel_id = int(arg.split('_')[1])
                    await self._process_get_link(update, channel_id)
                except (IndexError, ValueError):
                    await update.message.reply_text("❌ Invalid link request.")
                return
            
            # Handle referral code
            referral_code = arg
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
                await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
            # ENSURE USER HAS A REFERRAL LINK
            target_channel_id = -1001897244942
            referral_link = None
            
            # Check existing
            channel_key = str(target_channel_id)
            
            # DEBUG LOGGING
            if user_data:
                logger.info(f"Start CMD | User: {user.id} | Keys: {list(user_data.get('channels', {}).keys())}")
                if channel_key in user_data.get('channels', {}):
                     existing = user_data['channels'][channel_key].get('referral_link')
                     logger.info(f"Start CMD | Found existing link: {existing}")
            
            if user_data and user_data.get('channels') and channel_key in user_data['channels']:
                referral_link = user_data['channels'][channel_key].get('referral_link')
            
            # Generate if missing
            if not referral_link:
                try:
                    logger.info(f"Start CMD | No link found for {user.id}, generating new one.")
                    # Remove member_limit to avoid "10k" label and use standard links
                    referral_link = await self._create_trackable_invite_link(user.id, target_channel_id)
                except Exception as e:
                    logger.error(f"Error generating link in start command: {e}")
                    referral_link = self.referral_manager.generate_referral_link(user.id, target_channel_id)

            # Send main welcome message with the link
            welcome_message = BotMessages.WELCOME_PRIVATE.format(
                first_name=user.first_name,
                referral_link=referral_link,
                target=self.config.REFERRAL_TARGET
            )
            
            # Updated Buttons as per specific user request: Start, Status, Get Reward, Help
            keyboard = [
                # "Start" is technically what we just did, but we can offer a button to re-generate/show link
                [InlineKeyboardButton(BotMessages.BTN_CREATE_LINK, callback_data="start_link")], 
                [InlineKeyboardButton(BotMessages.BTN_MY_LINK, callback_data="mylink")],
                [InlineKeyboardButton(BotMessages.BTN_STATUS, callback_data="status")],
                [InlineKeyboardButton(BotMessages.BTN_GET_REWARD, callback_data="claim")],
                [InlineKeyboardButton(BotMessages.BTN_HELP, callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.effective_message.reply_text(
                "👋 Hi! I'm a referral bot. Add me as an admin to your channel to start using referral features!"
            )
    
    async def help_command(self, update: Update, context):
        """Handle /help command."""
        help_text = BotMessages.HELP_TEXT.format(target=self.config.REFERRAL_TARGET)
        await update.effective_message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context):
        """Handle /status command."""
        user_id = update.effective_user.id
        user_data = self.data_manager.get_user_data(user_id)
        
        target_channel_id = -1001897244942
        if not user_data or not user_data.get('channels'):
            await update.effective_message.reply_text(
                BotMessages.STATUS_EMPTY,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        status_text = BotMessages.STATUS_HEADER
        
        # Track processed channels to avoid duplicates if ID migration happened
        processed_channel_names = set()
        has_primary_channel = False
        
        # Helper to process a channel
        def add_channel_status(c_id, c_data):
            c_info = self.data_manager.get_channel_info(c_id)
            # Normalizing name for de-duplication
            c_name = c_info.get('name', 'Unknown Channel') if c_info else 'Unknown Channel'
            
            # If we've already displayed this channel name, skip (legacy ID fix)
            if c_name in processed_channel_names:
                return False
                
            processed_channel_names.add(c_name)
            
            succ_referrals = c_data.get('successful_referrals', 0)
            targ = self.config.REFERRAL_TARGET
            rew_claimed = c_data.get('rewards_claimed', 0)
            
            nonlocal status_text
            status_text += BotMessages.STATUS_CHANNEL_LINE.format(channel_name=c_name)
            status_text += BotMessages.STATUS_DETAILS.format(
                count=succ_referrals,
                target=targ,
                progress_bar=utils.get_progress_bar(succ_referrals, targ),
                claimed=rew_claimed
            )
            
            if succ_referrals >= targ:
                status_text += BotMessages.STATUS_READY_TO_CLAIM
            else:
                rem = targ - succ_referrals
                status_text += BotMessages.STATUS_NEED_MORE.format(rem=rem)
            
            status_text += "\n"
            return True

        # Loop through user channels
        for channel_id, channel_data in user_data['channels'].items():
            if str(channel_id) == str(target_channel_id):
                has_primary_channel = True
            add_channel_status(channel_id, channel_data)
        
        # If the user has data but NOT for the new primary ID, implies they are legacy.
        # But if the loop above covered the legacy channel name via the old ID, `processed_channel_names` handles it.
        # If nothing was added (e.g. data corrupt), add default.
        if not processed_channel_names:
             # Show default if new user with empty channels
             status_text += f"🔶 *EarnPro*\n"
             status_text += f"   • Referrals: 0/{self.config.REFERRAL_TARGET}\n"
             status_text += f"   • Progress: {utils.get_progress_bar(0, self.config.REFERRAL_TARGET)}\n"
             status_text += f"\n🎯 Need {self.config.REFERRAL_TARGET} more referrals to unlock rewards."
        
        keyboard = [
            [InlineKeyboardButton(BotMessages.BTN_GET_REWARD, callback_data="claim")],
            [InlineKeyboardButton(BotMessages.BTN_REFRESH, callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def claim_command(self, update: Update, context):
        """Handle /claim command."""
        user_id = update.effective_user.id
        user_data = self.data_manager.get_user_data(user_id)
        
        target_channel_id = -1001897244942
        channel_key = str(target_channel_id)
        
        successful_referrals = 0
        
        # Check new key first
        if user_data and 'channels' in user_data:
            if channel_key in user_data['channels']:
                successful_referrals = user_data['channels'][channel_key].get('successful_referrals', 0)
            else:
                # Fallback check for any channel using the legacy name (old ID)
                # Honor referrals recorded under the old channel name or the new one
                for c_id, c_data in user_data['channels'].items():
                     c_info = self.data_manager.get_channel_info(c_id)
                     if c_info and c_info.get('name') in ("EarnPro Elites Channel", "EarnPro"):
                         successful_referrals = max(successful_referrals, c_data.get('successful_referrals', 0))
        
        target = self.config.REFERRAL_TARGET
        
        if successful_referrals >= target:
            # ELIGIBLE
            claim_text = BotMessages.CLAIM_ELIGIBLE.format(
                count=successful_referrals,
                user_id=user_id
            )
        else:
            # NOT ELIGIBLE
            remaining = target - successful_referrals
            claim_text = BotMessages.CLAIM_LOCKED.format(
                count=successful_referrals,
                target=target,
                rem=remaining
            )
            
        await update.effective_message.reply_text(claim_text, parse_mode=ParseMode.MARKDOWN)

    async def mylink_command(self, update: Update, context):
        """Handle /mylink command and button."""
        user_id = update.effective_user.id
        user_data = self.data_manager.get_user_data(user_id)
        target_channel_id = -1001897244942
        channel_key = str(target_channel_id)
        
        referral_link = None
        if user_data and 'channels' in user_data and channel_key in user_data['channels']:
            referral_link = user_data['channels'][channel_key].get('referral_link')
            
        if referral_link:
             message = BotMessages.MY_LINK_MESSAGE.format(referral_link=referral_link)
        else:
             message = BotMessages.MY_LINK_MISSING
        
        # Add back button
        keyboard = [[InlineKeyboardButton(BotMessages.BTN_BACK_MENU, callback_data="start_link")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def admin_command(self, update: Update, context):
        """Handle /admin command for channel administrators."""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type == 'private':
            # REMOTE ADMIN DASHBOARD
            # Check if this is the super admin
            if user.id == self.config.SUPER_ADMIN_ID:
                channels = self.data_manager.get_all_channels()
                
                if not channels:
                    await update.effective_message.reply_text("❌ No channels registered yet.")
                    return
                
                message = "🛡️ *Remote Admin Dashboard*\n\nSelect a channel to view statistics:"
                keyboard = []
                
                for c_id, c_data in channels.items():
                    c_name = c_data.get('name', f'Channel {c_id}')
                    keyboard.append([InlineKeyboardButton(f"📊 {c_name}", callback_data=f"admin_stats_{c_id}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                return

            await update.effective_message.reply_text(
                "❌ Admin commands can only be used in channels where you're an admin."
            )
            return
        
        # Check permissions
        is_admin = False
        status_msg = "unknown"

        # 1. Check if sent by the Channel itself (Anonymous Admin)
        if update.effective_message.sender_chat and update.effective_message.sender_chat.id == chat.id:
            is_admin = True
            status_msg = "Channel Creator (Anonymous)"
        else:
            # 2. Check individual user status
            try:
                chat_member = await context.bot.get_chat_member(chat.id, user.id)
                status_msg = chat_member.status
                # logger.info(f"Admin CMD Check | Chat: {chat.title} | User: {user.id} | Status: {status_msg}")
                
                if chat_member.status in ['administrator', 'creator']:
                    is_admin = True
            except Exception as e:
                logger.error(f"Error checking admin status: {e}")
                
        if not is_admin:
            await update.effective_message.reply_text(f"❌ Permission Denied. Status: {status_msg}")
            return
        
        # Register or update channel
        self.data_manager.register_channel(chat.id, chat.title or "Unknown Channel")
        
        channel_stats = self.referral_manager.get_channel_stats(chat.id)
        
        admin_text = (
            f"🔧 *Channel Admin Panel*\n\n"
            f"📺 *{chat.title}*\n"
            f"📊 *Channel Statistics:*\n"
            f"• Total users: {channel_stats.get('total_users', 0)}\n"
            f"• Active referrers: {channel_stats.get('active_referrers', 0)}\n"
            f"• Total referrals: {channel_stats.get('total_referrals', 0)}\n"
            f"• Rewards claimed: {channel_stats.get('rewards_claimed', 0)}\n\n"
            f"🎯 *Settings:*\n"
            f"• Referral target: {self.config.REFERRAL_TARGET}\n"
            f"• Reward type: {self.config.REWARD_TYPE}\n"
        )
        
        await update.effective_message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)
    
    async def track_chat_member(self, update: Update, context):
        """Track when users join or leave channels."""
        # SECURITY CHECK
        chat = update.effective_chat
        val_chat_id = chat.id
        
        if chat.type in ['group', 'supergroup', 'channel']:
             if val_chat_id not in self.config.ALLOWED_CHAT_IDS:
                logger.warning(f"SECURITY: Bot active in unauthorized chat {val_chat_id} ({chat.title}).")
                # try:
                #     await chat.leave()
                # except Exception as e:
                #     logger.error(f"Failed to leave unauthorized chat {val_chat_id}: {e}")
                # return

        chat_member_update = update.chat_member
        # chat = update.effective_chat # Already defined above
        user = chat_member_update.new_chat_member.user
        
        # Skip bot updates
        if user.is_bot:
            return
        
        old_status = chat_member_update.old_chat_member.status
        new_status = chat_member_update.new_chat_member.status
        
        # Capture invite link if available
        invite_link = None
        if hasattr(chat_member_update, 'invite_link') and chat_member_update.invite_link:
            invite_link = chat_member_update.invite_link.invite_link
        
        # User joined the channel
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
            await self._handle_user_join(chat.id, user.id, user.first_name, invite_link=invite_link)
        
        # User left the channel
        elif old_status in ['member', 'administrator', 'creator'] and new_status in ['left', 'kicked']:
            await self._handle_user_leave(chat.id, user.id)
    
    async def _handle_user_join(self, chat_id: int, user_id: int, user_name: str, invite_link: str = None):
        """Handle when a user joins a channel."""
        logger.info(f"User {user_id} joined channel {chat_id} (Link: {invite_link})")
        
        # 1. Ensure user exists in our database immediately
        self.data_manager.ensure_user_exists(user_id, username=user_name, first_name=user_name)
        
        # Check if this was a referral join
        referrer_id = None
        
        # Case A: Pending referral (via deep link start param) (Priority)
        pending_referral = self.data_manager.get_pending_referral(user_id, chat_id)
        if pending_referral:
            referrer_id = pending_referral['referrer_id']
            self.data_manager.remove_pending_referral(user_id, chat_id)
            
        # Case B: Invite Link (via direct channel join link)
        elif invite_link:
            referrer_id = self._get_referrer_from_link(invite_link)

        # Process Referral if referrer found
        if referrer_id:
            logger.info(f"Processing referral: Referrer {referrer_id}, New User {user_id}")
            
            # Check if user already referred (prevent double counting validation)
            # note: process_successful_referral blindly adds, so we should check logic if needed.
            # But user WANTS to support re-joining for testing.
            # The issue is "tracking fails".
            
            referral_count = self.referral_manager.process_successful_referral(referrer_id, chat_id, user_id)
            
            # Notify referrer
            try:
                # INSTANT NOTIFICATION as requested
                new_member_display = f"@{user_name}" if user_name else "Someone"
                
                message = BotMessages.REFERRAL_NOTIFICATION.format(
                    new_member=new_member_display,
                    count=referral_count,
                    target=self.config.REFERRAL_TARGET
                )
                
                # Check for referral milestone
                if referral_count >= self.config.REFERRAL_TARGET:
                    message += BotMessages.REFERRAL_MILESTONE_REACHED.format(
                        target=self.config.REFERRAL_TARGET
                    )
                
                await self.application.bot.send_message(referrer_id, message, parse_mode=ParseMode.MARKDOWN)
                logger.info(f"Sent referral notification to {referrer_id}")
            except Exception as e:
                logger.error(f"Failed to notify referrer {referrer_id}: {e}")
        else:
            logger.info(f"No referrer found for user {user_id} in channel {chat_id}. Link used: {invite_link}")
        
        # Generate REAL channel invite link for the new user
        target_channel_id = -1001897244942
        
        # Force REUSE of existing link if available to avoid multiple links per user
        user_data = self.data_manager.get_user_data(user_id)
        referral_link = None
        channel_key = str(target_channel_id)
        
        if user_data and 'channels' in user_data and channel_key in user_data['channels']:
            referral_link = user_data['channels'][channel_key].get('referral_link')
            
        if not referral_link:
             referral_link = await self._create_trackable_invite_link(user_id, target_channel_id)
        
        # PREPARE MESSAGES
        
        # Message 1: The DM (Direct Message) - Ideal case
        dm_message = BotMessages.WELCOME_PRIVATE.format(
            first_name=user_name,
            referral_link=referral_link,
            target=self.config.REFERRAL_TARGET
        )
        
        # Message 2: The Group Fallback - If DM fails
        group_message = BotMessages.WELCOME_CHANNEL_FALLBACK.format(user_name=user_name)
        
        bot_username = self.config.BOT_USERNAME
        deep_link = f"https://t.me/{bot_username}?start=getlink_{chat_id}"
        
        group_keyboard = [
            [InlineKeyboardButton(BotMessages.BTN_CHANNEL_GET_LINK, url=deep_link)]
        ]
        group_reply_markup = InlineKeyboardMarkup(group_keyboard)

        # EXECUTION: Try DM first, then Fallback
        # We try to send the DM. If it fails (e.g. Forbidden: bot was blocked by the user),
        # we catch the exception and send the fallback message to the group.
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=dm_message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Sent welcome DM to user {user_id}")
            
        except Exception as e:
            # 2. DM Failed (User hasn't started bot), send to Group
            logger.info(f"Could not DM user {user_id} ({e}). Falling back to group message.")
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id, 
                    text=group_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=group_reply_markup
                )
                logger.info(f"Sent fallback welcome to group {chat_id}")
            except Exception as e2:
                logger.error(f"Failed to send welcome message to group {chat_id}: {e2}")
    
    async def _create_trackable_invite_link(self, user_id: int, chat_id: int) -> str:
        """Create a trackable invite link for the channel that actually invites people to the channel."""
        try:
            # Create a unique invite link for this user
            invite_link = await self.application.bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"Referral-{user_id}",  # Name to identify this link
                creates_join_request=False  # Direct join, no approval needed
            )
            
            # Store the referral mapping
            referral_code = utils.generate_referral_code(user_id, chat_id)
            self.data_manager.store_referral_code(referral_code, user_id, chat_id)
            
            # Store the invite link mapping for tracking
            self._store_invite_link_mapping(invite_link.invite_link, user_id, chat_id, referral_code)
            
            # CRITICAL FIX: Persist the link to the user's profile so it can be reused!
            # If we don't do this, the bot will generate a new link every time the user checks.
            try:
                user_data = self.data_manager.get_user_data(user_id)
                channel_key = str(chat_id)
                
                # Verify channel data structure exists
                if not user_data:
                    user_data = {'channels': {}}
                if 'channels' not in user_data:
                    user_data['channels'] = {}
                if channel_key not in user_data['channels']:
                     # Initialize if empty
                     user_data['channels'][channel_key] = {
                        'successful_referrals': 0,
                        'rewards_claimed': 0,
                        'referred_users': [],
                        'referral_history': []
                    }
                
                # SAVE THE LINK
                user_data['channels'][channel_key]['referral_link'] = invite_link.invite_link
                self.data_manager.save_user_data(user_id, user_data)
                logger.info(f"Persisted referral link {invite_link.invite_link} for user {user_id}")
                
            except Exception as e_persist:
                logger.error(f"Failed to persist referral link to user data: {e_persist}")

            logger.info(f"Created trackable invite link for user {user_id} in channel {chat_id}")
            return invite_link.invite_link
            
        except Exception as e:
            logger.error(f"Failed to create invite link for chat {chat_id}: {e}", exc_info=True)
            # Fallback to bot link if invite link creation fails
            return self.referral_manager.generate_referral_link(user_id, chat_id)
    
    async def _get_referrer_from_link(self, invite_link: str) -> Optional[int]:
        """Look up who created an invite link."""
        try:
            import json
            import os
            
            mapping_file = "data/invite_links.json"
            
            if not os.path.exists(mapping_file):
                return None
            
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
                
            if invite_link in mappings:
                return mappings[invite_link]['user_id']
                
            return None
                
        except Exception as e:
            logger.error(f"Failed to lookup invite link: {e}")
            return None
    
    def _store_invite_link_mapping(self, invite_link: str, user_id: int, chat_id: int, referral_code: str):
        """Store the mapping between invite link and user for tracking."""
        try:
            import json
            import os
            
            mapping_file = "data/invite_links.json"
            
            # Load existing mappings
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    mappings = json.load(f)
            else:
                mappings = {}
            
            # Store new mapping
            mappings[invite_link] = {
                "user_id": user_id,
                "chat_id": chat_id,
                "referral_code": referral_code,
                "created_at": utils.get_current_timestamp()
            }
            
            # Save mappings
            with open(mapping_file, 'w') as f:
                json.dump(mappings, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to store invite link mapping: {e}")
    
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
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Could not answer callback query: {e}")
        
        if query.data == "status":
            # Send status directly to the callback query
            await query.edit_message_text(
                text="📊 Checking your referral status...",
                reply_markup=None
            )
            await self._send_status_to_callback(query, context)
        elif query.data == "start_link":
            # Just run check_command info essentially, or better, reply with the link
            # We can't easily "call" start_command from a callback without a message context often, 
            # but we can edit the message or send a new one.
            # Easiest is to send the help/link message again.
            await self.start_command(update, context)
        elif query.data == "mylink":
            await self.mylink_command(update, context)
        elif query.data == "claim":
            await self.claim_command(update, context)
        elif query.data == "help":
            await self._send_help_to_callback(query, context)
        elif query.data.startswith("claim_"):
            channel_id = int(query.data.split("_")[1])
            await self._process_reward_claim(update, channel_id)
        elif query.data == "admin_dashboard":
             await self.admin_command(update, context) # Re-use logic
        elif query.data.startswith("get_link_"):
            channel_id = int(query.data.split("_")[2])
            await self._process_get_link(update, channel_id)
        elif query.data.startswith("admin_stats_"):
            channel_id = int(query.data.split("_")[2])
            await self._send_admin_stats_callback(query, channel_id)
            
    async def _send_admin_stats_callback(self, query, channel_id: int):
        """Send admin stats for a specific channel via callback."""
        # Verify admin
        if query.from_user.id != self.config.SUPER_ADMIN_ID:
             await query.edit_message_text("❌ Unauthorized.")
             return

        channel_info = self.data_manager.get_channel_info(channel_id)
        channel_name = channel_info.get('name', 'Unknown Channel') if channel_info else 'Unknown Channel'
        
        channel_stats = self.referral_manager.get_channel_stats(channel_id)
        
        admin_text = (
            f"🔧 *Channel Admin Panel*\n\n"
            f"📺 *{channel_name}*\n"
            f"📊 *Channel Statistics:*\n"
            f"• Total users: {channel_stats.get('total_users', 0)}\n"
            f"• Active referrers: {channel_stats.get('active_referrers', 0)}\n"
            f"• Total referrals: {channel_stats.get('total_referrals', 0)}\n"
            f"• Rewards claimed: {channel_stats.get('rewards_claimed', 0)}\n\n"
            f"🎯 *Settings:*\n"
            f"• Referral target: {self.config.REFERRAL_TARGET}\n"
            f"• Reward type: {self.config.REWARD_TYPE}\n"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_dashboard")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(admin_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def _send_status_to_callback(self, query, context):
        """Send status response to callback query."""
        user_id = query.from_user.id
        
        # Get all channels
        all_channels = self.data_manager.get_all_channels()
        
        if not all_channels:
            await query.edit_message_text(
                text="❌ No channels found. The bot needs to be added to channels first."
            )
            return
        
        status_text = "📊 **Your Referral Status:**\n\n"
        
        for channel_id, channel_info in all_channels.items():
            channel_name = channel_info.get('name', f'Channel {channel_id}')
            progress = self.referral_manager.get_user_progress(user_id, int(channel_id))
            
            status_text += f"🏢 **{channel_name}**\n"
            status_text += f"   └ Referrals: {progress['successful_referrals']}/{self.config.REFERRAL_TARGET}\n"
            status_text += f"   └ Rewards claimed: {progress['rewards_claimed']}\n"
            
            if progress['can_claim_reward']:
                status_text += f"   └ ✅ Ready to claim reward!\n"
            else:
                remaining = self.config.REFERRAL_TARGET - progress['successful_referrals']
                status_text += f"   └ 🎯 Need {remaining} more referrals\n"
            
            status_text += "\n"
        
        await query.edit_message_text(text=status_text, parse_mode='Markdown')
    
    async def _send_help_to_callback(self, query, context):
        """Send help response to callback query."""
        help_text = (
            "🤖 **Telegram Referral Bot Help**\n\n"
            "**Commands:**\n"
            "• `/start` - Get your referral link\n"
            "• `/status` - Check your progress\n"
            "• `/claim` - Claim your rewards\n"
            "• `/help` - Show this help message\n\n"
            "**How it works:**\n"
            "🔸 Get invited to channels and earn rewards\n"
            "🔸 Share your referral links to invite others\n"
            "🔸 Track your progress and claim rewards\n\n"
            "Need help? Contact the channel admin!"
        )
        
        await query.edit_message_text(text=help_text, parse_mode='Markdown')
    
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

    async def _process_get_link(self, update: Update, channel_id: int):
        """Process request to get referral link via button."""
        user_id = update.effective_user.id
        
        # Generate the trackable link
        referral_link = await self._create_trackable_invite_link(user_id, channel_id)
        
        channel_info = self.data_manager.get_channel_info(channel_id)
        channel_name = channel_info.get('name', 'the channel') if channel_info else 'the channel'
        
        message = (
            f"🔗 *Here is your unique referral link for {channel_name}:*\n\n"
            f"`{referral_link}`\n\n"
            f"Share this link to invite {self.config.REFERRAL_TARGET} friends and earn rewards!\n"
            f"Use /status to track your progress.\n\n"
            f"🆕 *New Member?*\n"
            f"If you don't have an account on EarnPro yet, register at [earnpro.org](https://earnpro.org) using this code:\n"
            f"`USRMH6RNBI3`"
        )
        
        # Send as a new message to the user
        await self.application.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Acknowledge the callback
        await update.callback_query.answer("Link sent!")
    
    async def handle_message(self, update: Update, context):
        """Handle regular text messages."""
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        logger.info(f"Received message in chat {chat_id} ({chat_type}) from {update.effective_user.first_name}")
        
        # Ignore messages from other bots
        if update.effective_user.is_bot:
            return
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
