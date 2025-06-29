"""
Data Manager for handling persistent storage of bot data.
Uses JSON files for simple data persistence.
"""

import json
import os
import logging
from typing import Dict, Optional, Any
from threading import Lock
import utils

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data persistence using JSON files."""
    
    def __init__(self):
        """Initialize the data manager."""
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.channels_file = os.path.join(self.data_dir, "channels.json")
        self.referrals_file = os.path.join(self.data_dir, "referrals.json")
        self.pending_file = os.path.join(self.data_dir, "pending.json")
        
        # Thread lock for file operations
        self.lock = Lock()
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist."""
        files_to_init = [
            self.users_file,
            self.channels_file,
            self.referrals_file,
            self.pending_file
        ]
        
        for file_path in files_to_init:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f)
                logger.info(f"Initialized {file_path}")
    
    def _load_json(self, file_path: str) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: str, data: Dict):
        """Save JSON data to file."""
        try:
            # Create a backup first
            backup_path = file_path + '.backup'
            if os.path.exists(file_path):
                os.rename(file_path, backup_path)
            
            # Save new data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Remove backup if save was successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            # Restore backup if save failed
            backup_path = file_path + '.backup'
            if os.path.exists(backup_path):
                os.rename(backup_path, file_path)
    
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get user data by user ID."""
        with self.lock:
            users = self._load_json(self.users_file)
            return users.get(str(user_id))
    
    def save_user_data(self, user_id: int, user_data: Dict):
        """Save user data."""
        with self.lock:
            users = self._load_json(self.users_file)
            users[str(user_id)] = user_data
            users[str(user_id)]['last_updated'] = utils.get_current_timestamp()
            self._save_json(self.users_file, users)
    
    def get_all_users(self) -> Dict:
        """Get all users data."""
        with self.lock:
            return self._load_json(self.users_file)
    
    def register_channel(self, channel_id: int, channel_name: str):
        """Register a new channel or update existing one."""
        with self.lock:
            channels = self._load_json(self.channels_file)
            channels[str(channel_id)] = {
                'name': channel_name,
                'registered_at': utils.get_current_timestamp(),
                'last_updated': utils.get_current_timestamp()
            }
            self._save_json(self.channels_file, channels)
        
        logger.info(f"Registered channel: {channel_id} - {channel_name}")
    
    def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        """Get channel information."""
        with self.lock:
            channels = self._load_json(self.channels_file)
            return channels.get(str(channel_id))
    
    def get_all_channels(self) -> Dict:
        """Get all channels data."""
        with self.lock:
            return self._load_json(self.channels_file)
    
    def store_referral_code(self, referral_code: str, user_id: int, channel_id: int):
        """Store a referral code mapping."""
        with self.lock:
            referrals = self._load_json(self.referrals_file)
            referrals[referral_code] = {
                'user_id': user_id,
                'channel_id': channel_id,
                'created_at': utils.get_current_timestamp()
            }
            self._save_json(self.referrals_file, referrals)
    
    def get_referral_data(self, referral_code: str) -> Optional[Dict]:
        """Get referral data by code."""
        with self.lock:
            referrals = self._load_json(self.referrals_file)
            return referrals.get(referral_code)
    
    def add_pending_referral(self, user_id: int, channel_id: int, referrer_id: int):
        """Add a pending referral (user clicked link but hasn't joined yet)."""
        with self.lock:
            pending = self._load_json(self.pending_file)
            key = f"{user_id}_{channel_id}"
            pending[key] = {
                'user_id': user_id,
                'channel_id': channel_id,
                'referrer_id': referrer_id,
                'timestamp': utils.get_current_timestamp()
            }
            self._save_json(self.pending_file, pending)
    
    def get_pending_referral(self, user_id: int, channel_id: int) -> Optional[Dict]:
        """Get pending referral data."""
        with self.lock:
            pending = self._load_json(self.pending_file)
            key = f"{user_id}_{channel_id}"
            return pending.get(key)
    
    def remove_pending_referral(self, user_id: int, channel_id: int):
        """Remove a pending referral."""
        with self.lock:
            pending = self._load_json(self.pending_file)
            key = f"{user_id}_{channel_id}"
            if key in pending:
                del pending[key]
                self._save_json(self.pending_file, pending)
    
    def cleanup_old_pending_referrals(self, max_age_hours: int = 24):
        """Clean up old pending referrals that are older than max_age_hours."""
        with self.lock:
            pending = self._load_json(self.pending_file)
            current_time = utils.get_current_timestamp()
            
            # Find expired referrals
            expired_keys = []
            for key, data in pending.items():
                timestamp = data.get('timestamp', 0)
                age_hours = (current_time - timestamp) / 3600
                if age_hours > max_age_hours:
                    expired_keys.append(key)
            
            # Remove expired referrals
            for key in expired_keys:
                del pending[key]
            
            if expired_keys:
                self._save_json(self.pending_file, pending)
                logger.info(f"Cleaned up {len(expired_keys)} expired pending referrals")
    
    def backup_data(self):
        """Create a backup of all data files."""
        import shutil
        from datetime import datetime
        
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = [
            self.users_file,
            self.channels_file,
            self.referrals_file,
            self.pending_file
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                shutil.copy2(file_path, backup_dir)
        
        logger.info(f"Data backup created: {backup_dir}")
        return backup_dir
    
    def get_stats(self) -> Dict:
        """Get overall bot statistics."""
        with self.lock:
            users = self._load_json(self.users_file)
            channels = self._load_json(self.channels_file)
            referrals = self._load_json(self.referrals_file)
            pending = self._load_json(self.pending_file)
            
            return {
                'total_users': len(users),
                'total_channels': len(channels),
                'total_referral_codes': len(referrals),
                'pending_referrals': len(pending)
            }
