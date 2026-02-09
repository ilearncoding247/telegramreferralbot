
import sys
import logging
from telegram.ext import Application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_fix():
    print("Verifying python-telegram-bot version...")
    try:
        import telegram
        print(f"Telegram version: {telegram.__version__}")
    except ImportError:
        print("Failed to import telegram module.")
        return 1

    print("Attempting to build Application with dummy token...")
    try:
        # This specific call triggered the AttributeError in v20.x on Python 3.13+
        # 'Updater' object has no attribute '_Updater__polling_cleanup_cb'
        app = Application.builder().token("123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ").build()
        print("Application built successfully! The fix works.")
        return 0
    except AttributeError as e:
        if "Updater" in str(e) and "_Updater__polling_cleanup_cb" in str(e):
            print(f"FAIL: Reproduced the AttributeError: {e}")
            print("The library version is still incompatible.")
            return 1
        else:
            print(f"Encountered unexpected AttributeError: {e}")
            return 1
    except Exception as e:
        print(f"Encountered unexpected error: {e}")
        # If it initiates updater, it might fail on other things, but if it passes the init, it's good.
        return 1

if __name__ == "__main__":
    sys.exit(verify_fix())
