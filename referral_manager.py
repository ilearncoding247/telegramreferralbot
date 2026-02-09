"""
Referral Manager for handling referral logic and tracking.
Manages referral links, user progress, and reward claims.
"""

import uuid
import logging
from typing import Dict, Optional, List
from data_manager import DataManager
from config import Config
import utils

logger = logging.getLogger(__name__)

class ReferralManager:
    """Manages all referral-related operations."""
    
    def __init__(self, data_manager=None):
        """Initialize the referral manager."""
        try:
            from data_manager import DataManager
        except ImportError:
            DataManager = None

        self.data_manager = data_manager if data_manager else DataManager()
        self.config = Config()
    
    def generate_referral_link(self, user_id: int, channel_id: int) -> str:
        """Generate a unique referral link for a user and channel."""
        # Create unique referral code
        referral_code = utils.generate_referral_code(user_id, channel_id)
        
        # Store referral data
        self.data_manager.store_referral_code(referral_code, user_id, channel_id)
        
        # Generate bot link as fallback (or primary if not using direct invites)
        bot_username = self.config.BOT_USERNAME.replace('@', '') # Ensure no @ prefix
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        
        logger.info(f"Generated referral link for user {user_id} in channel {channel_id}")
        return referral_link
    
    def process_successful_referral(self, referrer_id: int, channel_id: int, referred_user_id: int):
        """Process a successful referral when someone joins via referral link."""
        # Get referrer's data
        referrer_data = self.data_manager.get_user_data(referrer_id)
        if not referrer_data:
            referrer_data = {'channels': {}}
        
        # Initialize channel data if not exists
        channel_key = str(channel_id)
        if channel_key not in referrer_data['channels']:
            referrer_data['channels'][channel_key] = {
                'successful_referrals': 0,
                'rewards_claimed': 0,
                'referred_users': [],
                'referral_history': []
            }
        
        # Add the referral
        referrer_data['channels'][channel_key]['successful_referrals'] += 1
        referrer_data['channels'][channel_key]['referred_users'].append(referred_user_id)
        referrer_data['channels'][channel_key]['referral_history'].append({
            'user_id': referred_user_id,
            'timestamp': utils.get_current_timestamp(),
            'action': 'joined'
        })
        
        # Save updated data
        self.data_manager.save_user_data(referrer_id, referrer_data)
        
        logger.info(f"Processed successful referral: {referrer_id} -> {referred_user_id} in channel {channel_id}")
        
        return referrer_data['channels'][channel_key]['successful_referrals']
    
    def process_referral_leave(self, referrer_id: int, channel_id: int, left_user_id: int):
        """Process when a referred user leaves the channel."""
        # Get referrer's data
        referrer_data = self.data_manager.get_user_data(referrer_id)
        if not referrer_data:
            return
        
        channel_key = str(channel_id)
        if channel_key not in referrer_data['channels']:
            return
        
        # Check if this user was referred by this referrer
        if left_user_id in referrer_data['channels'][channel_key]['referred_users']:
            # Decrement successful referrals (but don't go below 0)
            if referrer_data['channels'][channel_key]['successful_referrals'] > 0:
                referrer_data['channels'][channel_key]['successful_referrals'] -= 1
            
            # Remove from referred users list
            referrer_data['channels'][channel_key]['referred_users'].remove(left_user_id)
            
            # Add to history
            referrer_data['channels'][channel_key]['referral_history'].append({
                'user_id': left_user_id,
                'timestamp': utils.get_current_timestamp(),
                'action': 'left'
            })
            
            # Save updated data
            self.data_manager.save_user_data(referrer_id, referrer_data)
            
            logger.info(f"Processed referral leave: {referrer_id} -> {left_user_id} in channel {channel_id}")
    
    def find_referrer(self, channel_id: int, user_id: int) -> Optional[int]:
        """Find who referred a specific user to a channel."""
        # This is a simplified approach - in a real implementation,
        # you might want to store this relationship more efficiently
        all_users = self.data_manager.get_all_users()
        
        for referrer_id, user_data in all_users.items():
            if 'channels' in user_data:
                channel_key = str(channel_id)
                if channel_key in user_data['channels']:
                    if user_id in user_data['channels'][channel_key].get('referred_users', []):
                        return int(referrer_id)
        
        return None
    
    def claim_reward(self, user_id: int, channel_id: int) -> Dict:
        """Process a reward claim."""
        user_data = self.data_manager.get_user_data(user_id)
        if not user_data:
            return {'success': False, 'message': 'User data not found.'}
        
        channel_key = str(channel_id)
        if channel_key not in user_data.get('channels', {}):
            return {'success': False, 'message': 'Channel data not found.'}
        
        channel_data = user_data['channels'][channel_key]
        successful_referrals = channel_data.get('successful_referrals', 0)
        rewards_claimed = channel_data.get('rewards_claimed', 0)
        
        # Calculate available rewards
        total_eligible_rewards = successful_referrals // self.config.REFERRAL_TARGET
        available_rewards = total_eligible_rewards - rewards_claimed
        
        if available_rewards <= 0:
            return {
                'success': False, 
                'message': f'No rewards available. You need {self.config.REFERRAL_TARGET} successful referrals per reward.'
            }
        
        # Claim the reward
        channel_data['rewards_claimed'] += 1
        self.data_manager.save_user_data(user_id, user_data)
        
        # Log the reward claim
        logger.info(f"User {user_id} claimed reward for channel {channel_id}")
        
        return {
            'success': True,
            'message': 'Reward claimed successfully!',
            'total_claimed': channel_data['rewards_claimed']
        }
    
    def get_user_progress(self, user_id: int, channel_id: int) -> Dict:
        """Get detailed progress information for a user in a specific channel."""
        user_data = self.data_manager.get_user_data(user_id)
        if not user_data:
            return {}
        
        channel_key = str(channel_id)
        if channel_key not in user_data.get('channels', {}):
            return {}
        
        channel_data = user_data['channels'][channel_key]
        successful_referrals = channel_data.get('successful_referrals', 0)
        rewards_claimed = channel_data.get('rewards_claimed', 0)
        
        return {
            'successful_referrals': successful_referrals,
            'rewards_claimed': rewards_claimed,
            'progress_percentage': min(100, (successful_referrals / self.config.REFERRAL_TARGET) * 100),
            'referrals_needed': max(0, self.config.REFERRAL_TARGET - successful_referrals),
            'available_rewards': (successful_referrals // self.config.REFERRAL_TARGET) - rewards_claimed,
            'referral_history': channel_data.get('referral_history', [])
        }
    
    def get_channel_stats(self, channel_id: int) -> Dict:
        """Get overall statistics for a channel."""
        # 1. OPTIMIZED PATH: Use DB aggregation if available
        if hasattr(self.data_manager, 'get_channel_aggregate_stats'):
            return self.data_manager.get_channel_aggregate_stats(channel_id)

        # 2. LEGACY PATH: Iterate all users (Inefficient)
        all_users = self.data_manager.get_all_users()
        channel_key = str(channel_id)
        
        total_users = 0
        active_referrers = 0
        total_referrals = 0
        rewards_claimed = 0
        
        for user_id, user_data in all_users.items():
            if 'channels' in user_data and channel_key in user_data['channels']:
                total_users += 1
                channel_data = user_data['channels'][channel_key]
                
                user_referrals = channel_data.get('successful_referrals', 0)
                if user_referrals > 0:
                    active_referrers += 1
                
                total_referrals += user_referrals
                rewards_claimed += channel_data.get('rewards_claimed', 0)
        
        return {
            'total_users': total_users,
            'active_referrers': active_referrers,
            'total_referrals': total_referrals,
            'rewards_claimed': rewards_claimed,
            'average_referrals_per_user': total_referrals / max(1, total_users)
        }
    
    def get_leaderboard(self, channel_id: int, limit: int = 10) -> List[Dict]:
        """Get top referrers for a channel."""
        all_users = self.data_manager.get_all_users()
        channel_key = str(channel_id)
        
        leaderboard = []
        
        for user_id, user_data in all_users.items():
            if 'channels' in user_data and channel_key in user_data['channels']:
                channel_data = user_data['channels'][channel_key]
                referrals = channel_data.get('successful_referrals', 0)
                
                if referrals > 0:
                    leaderboard.append({
                        'user_id': int(user_id),
                        'referrals': referrals,
                        'rewards_claimed': channel_data.get('rewards_claimed', 0)
                    })
        
        # Sort by referrals (descending)
        leaderboard.sort(key=lambda x: x['referrals'], reverse=True)
        
        return leaderboard[:limit]
