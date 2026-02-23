import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

async def check_webhook():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    print(f"🤖 Checking status for bot token: {token[:6]}...{token[-4:]}")
    
    # Get current webhook info from Telegram
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests.get(url).json()
    
    if response.get('ok'):
        info = response.get('result', {})
        current_url = info.get('url', 'None')
        pending_count = info.get('pending_update_count', 0)
        last_error_date = info.get('last_error_date')
        last_error_message = info.get('last_error_message')
        
        print(f"\n📡 Current Webhook URL: {current_url}")
        print(f"⏳ Pending updates: {pending_count}")
        
        if last_error_message:
            print(f"❌ Last Error Message: {last_error_message}")
        else:
            print("✅ No recent webhook errors reported by Telegram.")
            
        if webhook_url:
            if not current_url.startswith(webhook_url):
                print(f"\n⚠️ WARNING: Your .env WEBHOOK_URL ({webhook_url}) does not match the one set on Telegram!")
            else:
                print("\n✅ Webhook URL matches your configuration.")
    else:
        print(f"❌ Error fetching webhook info: {response.get('description')}")

if __name__ == "__main__":
    asyncio.run(check_webhook())
