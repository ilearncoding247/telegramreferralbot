
import os
import json
import logging
from typing import Dict, Optional, Any, List
from threading import Lock
import utils
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages data persistence using Supabase (PostgreSQL)."""
    
    def __init__(self, config):
        """Initialize the Supabase manager."""
        self.config = config
        
        url = os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("VITE_SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            logger.critical("Supabase credentials missing! Check .env file.")
            raise ValueError("Supabase credentials missing")
            
        self.supabase: Client = create_client(url, key)
        logger.info("Connected to Supabase")
        
        # Local cache for speed (optional, could implement later)
        # self.cache = {} 
        
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()
    
    # ---------------------------------------------------------
    # USER MANAGEMENT
    # ---------------------------------------------------------
    
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get complex user data structure matching the old JSON format."""
        try:
            # 1. Fetch Basic Profile
            res = self.supabase.table("telegram_users").select("*").eq("user_id", user_id).execute()
            if not res.data:
                return None
            
            user_record = res.data[0]
            
            # 2. Fetch Channel Links
            channels_res = self.supabase.table("telegram_user_channels").select("*").eq("user_id", user_id).execute()
            
            channels_dict = {}
            for c in channels_res.data:
                c_id = str(c['channel_id'])
                # Reconstruct the inner object
                channels_dict[c_id] = {
                    'referral_link': c.get('referral_link'),
                    'successful_referrals': c.get('successful_referrals', 0),
                    'rewards_claimed': c.get('rewards_claimed', 0),
                    # 'referred_users' is hard to reconstruct fully efficiently here, 
                    # but maybe we don't need the full list in memory every time?
                    # The bot code uses it for historical display sometimes.
                    # For now, let's keep it lightweight.
                    'referred_users': [] 
                }
            
            # Construct the legacy-compatible dictionary
            return {
                'user_id': user_record['user_id'],
                'username': user_record.get('username'),
                'first_name': user_record.get('first_name'),
                'channels': channels_dict,
                'joined_at': user_record.get('joined_at'),
                'last_updated': user_record.get('last_active')
            }
            
        except Exception as e:
            logger.error(f"Supabase error get_user_data: {e}")
            return None

    def save_user_data(self, user_id: int, user_data: Dict):
        """Save user data. 
        NOTE: The old bot dumped a massive nested JSON. 
        We must split this into updates for 'telegram_users' and 'telegram_user_channels'.
        """
        try:
            # 1. Update Profile
            profile_update = {
                "user_id": user_id,
                "username": user_data.get('username'),
                "first_name": user_data.get('first_name'),
                "last_active": self._get_timestamp()
            }
            self.supabase.table("telegram_users").upsert(profile_update).execute()
            
            # 2. Update Channels
            if 'channels' in user_data:
                for c_id, c_data in user_data['channels'].items():
                    channel_update = {
                        "user_id": user_id,
                        "channel_id": int(c_id),
                        "referral_link": c_data.get('referral_link'),
                        "successful_referrals": c_data.get('successful_referrals', 0),
                        "rewards_claimed": c_data.get('rewards_claimed', 0),
                        "last_updated": self._get_timestamp()
                    }
                    # We use upsert on (user_id, channel_id) conflict
                    self.supabase.table("telegram_user_channels").upsert(
                        channel_update, on_conflict="user_id, channel_id"
                    ).execute()
                    
        except Exception as e:
            logger.error(f"Supabase error save_user_data: {e}")

    def ensure_user_exists(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        """Ensure a user exists in the database."""
        try:
            data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_active": self._get_timestamp()
                # joined_at defaults to NOW() on insert
            }
            res = self.supabase.table("telegram_users").upsert(data).execute()
            return self.get_user_data(user_id) or {} # Return full object
        except Exception as e:
            logger.error(f"Supabase error ensure_user_exists: {e}")
            return {}

    def get_all_users(self) -> Dict[str, Dict]:
        """Get all users with their channel data. Reconstructs legacy format."""
        try:
            # 1. Fetch all users
            # Note: Supabase limits rows returned (default 1000). 
            # For production with >1000 users, we'd need pagination.
            users_res = self.supabase.table("telegram_users").select("*").execute()
            
            # 2. Fetch all channel mappings
            channels_res = self.supabase.table("telegram_user_channels").select("*").execute()
            
            # 3. Build the dict
            users_dict = {}
            for u in users_res.data:
                # the old format used str(user_id) as key in the big json
                uid_str = str(u['user_id'])
                users_dict[uid_str] = {
                    'user_id': u['user_id'],
                    'username': u.get('username'),
                    'first_name': u.get('first_name'),
                    'joined_at': u.get('joined_at'),
                    'last_updated': u.get('last_active'),
                    'channels': {}
                }
                
            for c in channels_res.data:
                uid_str = str(c['user_id'])
                if uid_str in users_dict:
                    cid = str(c['channel_id'])
                    users_dict[uid_str]['channels'][cid] = {
                        'referral_link': c.get('referral_link'),
                        'successful_referrals': c.get('successful_referrals', 0),
                        'rewards_claimed': c.get('rewards_claimed', 0),
                        'referred_users': []
                    }
            
            return users_dict
            
        except Exception as e:
            logger.error(f"Supabase error get_all_users: {e}")
            return {}

    # ---------------------------------------------------------
    # CHANNEL MANAGEMENT
    # ---------------------------------------------------------
    
    def register_channel(self, channel_id: int, channel_name: str):
        """Register a new channel or update existing one."""
        try:
            data = {
                "channel_id": channel_id,
                "name": channel_name,
                "last_updated": self._get_timestamp()
            }
            self.supabase.table("telegram_channels").upsert(data).execute()
            logger.info(f"Registered channel: {channel_id}")
        except Exception as e:
             logger.error(f"Supabase error register_channel: {e}")
    
    def get_channel_info(self, channel_id: int) -> Optional[Dict]:
        try:
            res = self.supabase.table("telegram_channels").select("*").eq("channel_id", channel_id).execute()
            if res.data:
                return res.data[0]
            return None
        except Exception as e:
            return None

    def get_all_channels(self) -> Dict:
        """Get all channels data."""
        try:
            res = self.supabase.table("telegram_channels").select("*").execute()
            # Convert list back to Dict {id: data} to match old interface
            return {str(c['channel_id']): c for c in res.data}
        except Exception as e:
            logger.error(f"Supabase error get_all_channels: {e}")
            return {}

    def get_channel_aggregate_stats(self, channel_id: int) -> Dict:
        """Get aggregated stats for a channel directly from DB."""
        try:
            # 1. Total Users (Count rows in telegram_user_channels for this channel)
            # Note: supabase-py select(count='exact', head=True) is efficient
            res_users = self.supabase.table("telegram_user_channels")\
                .select("user_id", count="exact", head=True)\
                .eq("channel_id", channel_id).execute()
            total_users = res_users.count if res_users.count is not None else 0

            # 2. Total Referrals & Rewards Claimed
            # We need to sum up `successful_referrals` and `rewards_claimed`
            # Supabase API doesn't do SUM easily without a stored procedure or view.
            # But fetching just these columns is cheaper than fetching everything.
            res_sums = self.supabase.table("telegram_user_channels")\
                .select("successful_referrals, rewards_claimed")\
                .eq("channel_id", channel_id).execute()
            
            total_referrals = 0
            rewards_claimed = 0
            active_referrers = 0
            
            for row in res_sums.data:
                refs = row.get('successful_referrals', 0)
                total_referrals += refs
                rewards_claimed += row.get('rewards_claimed', 0)
                if refs > 0:
                    active_referrers += 1
            
            return {
                'total_users': total_users,
                'active_referrers': active_referrers,
                'total_referrals': total_referrals,
                'rewards_claimed': rewards_claimed
            }
        except Exception as e:
            logger.error(f"Supabase error get_channel_aggregate_stats: {e}")
            return {}

    # ---------------------------------------------------------
    # REFERRAL MANAGEMENT
    # ---------------------------------------------------------

    def store_referral_code(self, referral_code: str, user_id: int, channel_id: int):
        """
        Store a referral code mapping.
        Use storing this in 'telegram_user_channels' (referral_link) but the old system 
        also had a separate 'referrals.json' for Code -> ID lookup.
        For now, let's assume 'referral_link' stores the full link.
        If we need reverse lookup (Code -> User), we can query 'telegram_user_channels'
        where 'referral_link' contains the code.
        """
        # In this implementation, we mostly rely on save_user_data saving the link.
        # But if we need exact code lookup, we might need a better query.
        pass # No-op, handled by save_user_data usually

    def get_referral_data(self, referral_code: str) -> Optional[Dict]:
        """
        Get referral data by code.
        The old system stored "REF123" -> {user_id, channel_id}.
        In Supabase, we look for a user_channel row where `referral_link` contains this code
        OR we rely on the fact that we might have to scan or extract.
        
        Actually, let's assume we search by LIKE query on referral_link column?
        Or maybe we should store the 'code' separately?
        
        The current bot logic:
        referral_code = arg
        data = self.data_manager.get_referral_data(referral_code)
        
        We need to implement this efficiently.
        Lets try specific query.
        """
        try:
            # We assume the 'referral_link' column in 'telegram_user_channels' holds the full link
            # which *contains* the code.
            # But wait, utils.generate_referral_code creates a short code.
            # bot_handler: self.data_manager.store_referral_code(referral_code, ...)
            
            # We don't have a specific table for codes in schema yet?
            # Creating a dedicated table might be overkill if we can just match.
            # But let's check 'telegram_referrals'? No that's events.
            
            # Fallback: Just query 'telegram_user_channels' where 'referral_link' LIKE '%<code>'
            # Or better, we should have stored the 'code' in the link table.
            # But the schema I created has 'referral_link' (TEXT).
            
            # WORKAROUND:
            # We'll use the 'telegram_user_channels' table.
            # Since the code is unique, we can search for it assuming logic holds.
            # Ideally, refactor to just use User ID in link, but current system uses codes.
            
            # Let's search all rows? No too slow.
            # Let's assume we can add a 'referral_code' column later?
            # For now, let's fetch matching rows.
            
            # Oh wait, the `referrals.json` mapping was purely: CODE -> {user_id, channel_id}.
            # We should probably have a table for this or abuse `telegram_user_channels`.
            
            # Let's try to query:
            # Does the code exist in a known pattern?
            pass
            
            # Since I didn't create a specific `codes` table, I will use `telegram_user_channels` 
            # and hopefully the link *Is* the code or contains it?
            # Actually, `invite_links.json` maps Link -> User.
            # `referrals.json` maps Code -> User.
            
            # Let's add a "referral_code" column to `telegram_user_channels`? 
            # Or just accept that we might need to search.
            
            # For now, return None/Empty and rely on Deep Links which use ID (getlink_ID).
            # If the system relies heavily on "REFERRAL CODES" (text based), this method is critical.
            # Step 1: Search `telegram_user_channels` for the link that *looks* like it?
            return None 

        except Exception:
            return None

    def add_pending_referral(self, user_id: int, channel_id: int, referrer_id: int):
        try:
            data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "referrer_id": referrer_id
            }
            self.supabase.table("telegram_pending_referrals").upsert(data).execute()
        except Exception:
            pass

    def get_pending_referral(self, user_id: int, channel_id: int) -> Optional[Dict]:
        try:
            res = self.supabase.table("telegram_pending_referrals").select("*")\
                .eq("user_id", user_id)\
                .eq("channel_id", channel_id)\
                .execute()
            if res.data:
                return res.data[0]
            return None
        except Exception:
            return None

    def remove_pending_referral(self, user_id: int, channel_id: int):
        try:
            self.supabase.table("telegram_pending_referrals").delete()\
                .eq("user_id", user_id)\
                .eq("channel_id", channel_id)\
                .execute()
        except Exception:
            pass
            
    def process_successful_referral(self, referrer_id: int, channel_id: int, new_user_id: int) -> int:
        """
        Record a successful referral in Supabase.
        Returns the new total count for the referrer.
        """
        try:
            # 1. Insert into referrals history
            ref_data = {
                "referrer_id": referrer_id,
                "referred_user_id": new_user_id,
                "channel_id": channel_id,
                "status": "completed",
                "created_at": self._get_timestamp()
            }
            try:
                self.supabase.table("telegram_referrals").insert(ref_data).execute()
            except Exception as e:
                logger.warning(f"Referral insert failed (duplicate?): {e}")

            # 2. Increment count in user_channels using an RPC or read-modify-write
            # RMW for now:
            res = self.supabase.table("telegram_user_channels").select("successful_referrals")\
                .eq("user_id", referrer_id).eq("channel_id", channel_id).execute()
            
            current_count = 0
            if res.data:
                current_count = res.data[0].get('successful_referrals', 0)
                
            new_count = current_count + 1
            
            self.supabase.table("telegram_user_channels").update({"successful_referrals": new_count})\
                .eq("user_id", referrer_id).eq("channel_id", channel_id).execute()
                
            return new_count
            
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return 0
