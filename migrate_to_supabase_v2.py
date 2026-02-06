
import os
import json
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing Supabase credentials in .env")
    exit(1)

# Initialize Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = "data"

def load_json(filename: str) -> Dict:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_timestamp(ts_val):
    """Convert timestamp to ISO format or return Now."""
    if isinstance(ts_val, (int, float)):
        return datetime.fromtimestamp(ts_val).isoformat()
    return datetime.now().isoformat()

async def migrate_users_and_channels():
    print("🚀 Starting Migration...")
    
    users = load_json("users.json")
    channels = load_json("channels.json")
    
    # 1. Migrate Channels
    print(f"📦 Migrating {len(channels)} Channels...")
    for c_id, c_data in channels.items():
        try:
            data = {
                "channel_id": int(c_id),
                "name": c_data.get("name", "Unknown"),
                "created_at": get_timestamp(c_data.get("registered_at")),
                "last_updated": get_timestamp(c_data.get("last_updated"))
            }
            res = supabase.table("telegram_channels").upsert(data).execute()
        except Exception as e:
            print(f"⚠️ Failed to migrate channel {c_id}: {e}")

    # Valid Channel IDs cache
    valid_channel_ids = set(int(k) for k in channels.keys())

    # 2. Migrate Users
    print(f"busts in silhouette Migrating {len(users)} Users...")
    
    user_records = []
    user_channel_records = []
    
    for u_id, u_data in users.items():
        try:
            user_id = int(u_id)
        except ValueError:
            print(f"⚠️ Skipping invalid user ID key: {u_id}")
            continue
        
        # User Record
        user_records.append({
            "user_id": user_id,
            "username": u_data.get("username"),
            "first_name": u_data.get("first_name"),
            "joined_at": get_timestamp(u_data.get("joined_at")),
            "last_active": get_timestamp(u_data.get("last_updated"))
        })
        
        # User-Channel Links
        if "channels" in u_data:
            for c_id, c_details in u_data["channels"].items():
                try:
                    channel_id_int = int(c_id)
                    if channel_id_int not in valid_channel_ids:
                        print(f"⚠️ Skipping orphan channel data for user {user_id} (Channel {c_id} not in channels.json)")
                        continue
                        
                    user_channel_records.append({
                        "user_id": user_id,
                        "channel_id": channel_id_int,
                        "referral_link": c_details.get("referral_link"),
                        "successful_referrals": c_details.get("successful_referrals", 0),
                        "rewards_claimed": c_details.get("rewards_claimed", 0),
                        "last_updated": datetime.now().isoformat()
                    })
                except Exception:
                    continue

    # Batch Insert Users
    if user_records:
        try:
            # Upsert in batches of 100
            for i in range(0, len(user_records), 100):
                batch = user_records[i:i+100]
                supabase.table("telegram_users").upsert(batch).execute()
            print(f"✅ Migrated {len(user_records)} Users")
        except Exception as e:
            print(f"❌ Failed to migrate users: {e}")

    # Batch Insert User Channels
    if user_channel_records:
        try:
            for i in range(0, len(user_channel_records), 100):
                batch = user_channel_records[i:i+100]
                supabase.table("telegram_user_channels").upsert(batch).execute()
            print(f"✅ Migrated {len(user_channel_records)} User-Channel Links")
        except Exception as e:
            print(f"❌ Failed to migrate user channels: {e}")

async def migrate_referrals():
    # Only if we can reconstruct them. 
    # The JSON structure for referrals is: Code -> {user_id, channel_id}
    # But it doesn't store "Who used this code".
    # Wait, `users.json` > `channels` > `referred_users` (List of IDs)?
    
    print("READING REFERRAL HISTORY...")
    users = load_json("users.json")
    
    referral_events = []
    
    for u_id, u_data in users.items():
        try:
            referrer_id = int(u_id)
        except ValueError:
            continue
            
        if "channels" in u_data:
            for c_id, c_details in u_data["channels"].items():
                channel_id = int(c_id)
                referred_users = c_details.get("referred_users", [])
                
                for invited_id in referred_users:
                    referral_events.append({
                        "referrer_id": referrer_id,
                        "referred_user_id": int(invited_id),
                        "channel_id": channel_id,
                        "status": "completed",
                        "created_at": datetime.now().isoformat() # We don't have exact timestamp of invite in this list
                    })
    
    print(f"🔗 Found {len(referral_events)} referral connections.")
    
    if referral_events:
        try:
             # We must ensure all 'referred_user_id' exist in telegram_users first.
             # In the loop above (migrate_users), we inserted ALL users found in users.json.
             # If a referred user is NOT in users.json (e.g. they joined but never started bot?), 
             # then we might have a constraint error.
             # Supabase upsert will fail if foreign key missing.
             
             # For safety, let's create "Stub" users for any missing IDs
             existing_ids = set(int(u) for u in users.keys())
             missing_ids = set()
             for ev in referral_events:
                 if ev["referred_user_id"] not in existing_ids:
                     missing_ids.add(ev["referred_user_id"])
            
             if missing_ids:
                 print(f"⚠️ Found {len(missing_ids)} referred users who have no profile. Creating Stubs...")
                 stubs = [{"user_id": uid, "first_name": "Unknown(Stub)"} for uid in missing_ids]
                 supabase.table("telegram_users").upsert(stubs).execute()
            
             for i in range(0, len(referral_events), 100):
                batch = referral_events[i:i+100]
                supabase.table("telegram_referrals").upsert(batch, on_conflict="referred_user_id, channel_id").execute()
             print("✅ Referral History Migrated")
             
        except Exception as e:
            print(f"❌ Failed to migrate referrals: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_users_and_channels())
    asyncio.run(migrate_referrals())
    print("🎉 Migration Complete")
