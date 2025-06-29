"""
Utility functions for the Telegram Referral Bot.
Contains helper functions for encoding, decoding, and formatting.
"""

import uuid
import base64
import json
import time
import hashlib
import logging
from typing import Dict, Optional, Any
import re

logger = logging.getLogger(__name__)

def generate_referral_code(user_id: int, channel_id: int) -> str:
    """Generate a unique referral code for a user and channel."""
    # Create a unique identifier based on user_id, channel_id, and timestamp
    timestamp = int(time.time())
    data = f"{user_id}_{channel_id}_{timestamp}"
    
    # Create a hash for uniqueness
    hash_obj = hashlib.md5(data.encode())
    hash_str = hash_obj.hexdigest()[:8]
    
    # Combine with base64 encoded data for the actual referral code
    referral_data = {
        'referrer_id': user_id,
        'channel_id': channel_id,
        'timestamp': timestamp,
        'hash': hash_str
    }
    
    # Encode to base64
    json_str = json.dumps(referral_data)
    encoded = base64.b64encode(json_str.encode()).decode()
    
    # Make it URL-safe and shorter
    code = encoded.replace('+', '-').replace('/', '_').replace('=', '')
    
    return code

def decode_referral_code(referral_code: str) -> Optional[Dict]:
    """Decode a referral code back to original data."""
    try:
        # Restore base64 padding and characters
        code = referral_code.replace('-', '+').replace('_', '/')
        
        # Add padding if needed
        padding = 4 - (len(code) % 4)
        if padding != 4:
            code += '=' * padding
        
        # Decode from base64
        decoded = base64.b64decode(code).decode()
        referral_data = json.loads(decoded)
        
        # Validate required fields
        required_fields = ['referrer_id', 'channel_id', 'timestamp']
        if not all(field in referral_data for field in required_fields):
            logger.warning(f"Invalid referral code structure: {referral_code}")
            return None
        
        return referral_data
        
    except Exception as e:
        logger.warning(f"Failed to decode referral code {referral_code}: {e}")
        return None

def get_current_timestamp() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())

def format_timestamp(timestamp: int) -> str:
    """Format timestamp to human-readable string."""
    try:
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)

def get_progress_bar(current: int, target: int, length: int = 10) -> str:
    """Generate a progress bar string."""
    if target <= 0:
        return "▓" * length
    
    progress = min(1.0, current / target)
    filled = int(progress * length)
    empty = length - filled
    
    return "▓" * filled + "░" * empty

def format_large_number(number: int) -> str:
    """Format large numbers with appropriate suffixes."""
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return f"{number/1000:.1f}K"
    elif number < 1000000000:
        return f"{number/1000000:.1f}M"
    else:
        return f"{number/1000000000:.1f}B"

def sanitize_channel_name(name: str) -> str:
    """Sanitize channel name for safe storage and display."""
    if not name:
        return "Unknown Channel"
    
    # Remove potentially problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:47] + "..."
    
    return sanitized or "Unknown Channel"

def validate_user_id(user_id: Any) -> bool:
    """Validate if user_id is a valid Telegram user ID."""
    try:
        uid = int(user_id)
        return uid > 0 and uid < 10**10  # Reasonable bounds for Telegram user IDs
    except (ValueError, TypeError):
        return False

def validate_channel_id(channel_id: Any) -> bool:
    """Validate if channel_id is a valid Telegram channel ID."""
    try:
        cid = int(channel_id)
        # Telegram channel IDs are typically negative and quite large
        return cid < 0 and abs(cid) > 10**9
    except (ValueError, TypeError):
        return False

def generate_unique_id() -> str:
    """Generate a unique ID string."""
    return str(uuid.uuid4())

def escape_markdown(text: str) -> str:
    """Escape markdown special characters in text."""
    if not text:
        return ""
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def calculate_referral_rate(successful: int, total_attempts: int) -> float:
    """Calculate referral success rate."""
    if total_attempts == 0:
        return 0.0
    return (successful / total_attempts) * 100

def get_time_difference_string(timestamp: int) -> str:
    """Get human-readable time difference from timestamp to now."""
    now = get_current_timestamp()
    diff = now - timestamp
    
    if diff < 60:
        return f"{diff} seconds ago"
    elif diff < 3600:
        return f"{diff // 60} minutes ago"
    elif diff < 86400:
        return f"{diff // 3600} hours ago"
    else:
        return f"{diff // 86400} days ago"

def chunk_list(lst: list, chunk_size: int) -> list:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def is_valid_telegram_username(username: str) -> bool:
    """Validate if username is a valid Telegram username format."""
    if not username:
        return False
    
    # Remove @ if present
    if username.startswith('@'):
        username = username[1:]
    
    # Check format: 5-32 characters, letters, digits, underscores
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer with default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with default."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int = 30, time_window: int = 60):
        """Initialize rate limiter."""
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if a call can be made within rate limits."""
        now = get_current_timestamp()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a call."""
        self.calls.append(get_current_timestamp())

def create_deep_link(bot_username: str, payload: str) -> str:
    """Create a Telegram deep link."""
    return f"https://t.me/{bot_username}?start={payload}"

def parse_deep_link(text: str) -> Optional[str]:
    """Extract payload from a Telegram deep link."""
    pattern = r'https://t\.me/\w+\?start=([^&\s]+)'
    match = re.search(pattern, text)
    return match.group(1) if match else None
