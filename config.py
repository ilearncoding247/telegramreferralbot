"""
Configuration settings for the Telegram Referral Bot.
Contains all configurable parameters and settings.
"""

import os

class Config:
    """Configuration class for the bot."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        
        # Bot settings
        self.BOT_USERNAME = os.getenv('BOT_USERNAME', 'officialearnpro')  # Set this to your bot's username
        
        # Referral settings
        self.REFERRAL_TARGET = 10  # Hardcoded as per request
        self.REWARD_TYPE = os.getenv('REWARD_TYPE', 'Premium Access')  # Type of reward
        self.SUPER_ADMIN_ID = 7803181156  # Hardcoded Super Admin for Remote Dashboard
        
        # Database settings
        self.DATA_BACKUP_INTERVAL = int(os.getenv('DATA_BACKUP_INTERVAL', '3600'))  # Backup interval in seconds
        self.CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '86400'))  # Cleanup interval in seconds
        
        # Bot behavior settings
        self.MAX_REFERRAL_LINK_AGE = int(os.getenv('MAX_REFERRAL_LINK_AGE', '86400'))  # Max age for referral links in seconds
        self.PENDING_REFERRAL_TIMEOUT = int(os.getenv('PENDING_REFERRAL_TIMEOUT', '3600'))  # Timeout for pending referrals
        
        # Logging settings
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
        
        # Rate limiting
        self.MAX_REFERRALS_PER_USER = int(os.getenv('MAX_REFERRALS_PER_USER', '1000'))  # Max referrals per user
        self.MAX_CHANNELS_PER_USER = int(os.getenv('MAX_CHANNELS_PER_USER', '50'))  # Max channels per user
        
        # Notification settings
        self.NOTIFY_ON_REFERRAL = os.getenv('NOTIFY_ON_REFERRAL', 'true').lower() == 'true'
        self.NOTIFY_ON_LEAVE = os.getenv('NOTIFY_ON_LEAVE', 'true').lower() == 'true'
        self.NOTIFY_ON_REWARD = os.getenv('NOTIFY_ON_REWARD', 'true').lower() == 'true'
        
        # Admin settings
        self.ADMIN_IDS = self._parse_admin_ids(os.getenv('ADMIN_IDS', ''))
        
        # Feature flags
        self.ENABLE_LEADERBOARD = os.getenv('ENABLE_LEADERBOARD', 'true').lower() == 'true'
        self.ENABLE_STATISTICS = os.getenv('ENABLE_STATISTICS', 'true').lower() == 'true'
        self.ENABLE_REWARDS = os.getenv('ENABLE_REWARDS', 'true').lower() == 'true'
        
        # Security: Whitelisted Chat IDs
        # Channel: Official EarnPro Channel (-1001897244942, https://t.me/officialearnpro)
        # Group: EarnPro Chats Group (-1003629306518, https://t.me/earnprochats)
        # Removed legacy/previous group IDs that were banned.
        self.ALLOWED_CHAT_IDS = [-1001897244942, -1003629306518]
        
        # Validation
        self._validate_config()
    
    def _parse_admin_ids(self, admin_ids_str: str) -> list:
        """Parse comma-separated admin IDs."""
        if not admin_ids_str:
            return []
        
        try:
            return [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
        except ValueError:
            return []
    
    def _validate_config(self):
        """Validate configuration values."""
        if self.REFERRAL_TARGET <= 0:
            raise ValueError("REFERRAL_TARGET must be greater than 0")
        
        if self.DATA_BACKUP_INTERVAL < 300:  # Minimum 5 minutes
            raise ValueError("DATA_BACKUP_INTERVAL must be at least 300 seconds")
        
        if self.MAX_REFERRALS_PER_USER <= 0:
            raise ValueError("MAX_REFERRALS_PER_USER must be greater than 0")
        
        if self.MAX_CHANNELS_PER_USER <= 0:
            raise ValueError("MAX_CHANNELS_PER_USER must be greater than 0")
    
    def get_reward_message(self, rewards_claimed: int) -> str:
        """Get reward message based on number of rewards claimed."""
        if rewards_claimed == 1:
            return f"🎉 Congratulations! You've earned your first {self.REWARD_TYPE}!"
        elif rewards_claimed <= 5:
            return f"🎊 Amazing! You've earned {rewards_claimed} {self.REWARD_TYPE} rewards!"
        else:
            return f"🏆 Incredible! You're a referral champion with {rewards_claimed} {self.REWARD_TYPE} rewards!"
    
    def get_progress_message(self, current: int, target: int) -> str:
        """Get progress message based on current referrals and target."""
        if current == 0:
            return f"🚀 Start sharing your referral link to get your first member!"
        elif current < target // 2:
            return f"📈 Great start! You're {current}/{target} towards your reward!"
        elif current < target:
            remaining = target - current
            return f"🔥 So close! Just {remaining} more referrals to earn your reward!"
        else:
            return f"✅ Target reached! You can claim your reward now!"
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self.ADMIN_IDS
    
    def __str__(self):
        """String representation of config."""
        return f"Config(referral_target={self.REFERRAL_TARGET}, reward_type='{self.REWARD_TYPE}')"
