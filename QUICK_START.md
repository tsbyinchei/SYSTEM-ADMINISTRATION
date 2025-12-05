# 🚀 QUICK START - PHIÊN BẢN TỐI ƯU V10

> **Developer:** TsByin  
> **Version:** 2.0 (Quick Start Guide)

## **5 BƯỚC NHANH**

### **1️⃣ Cài Đặt Thư Viện Mới**

```powershell
pip install python-dotenv
pip install -r requirements.txt
```

### **2️⃣ Cấu Hình .env**

```bash
# Mở file .env và sửa:
API_TOKEN=YOUR_TELEGRAM_TOKEN_HERE
ADMIN_ID=YOUR_ADMIN_ID_HERE
```

**Lưu lại file.**

### **3️⃣ Kiểm Tra Config**

```powershell
python -c "from config import API_TOKEN, ADMIN_ID; print('✅ Config OK')"
```

### **4️⃣ Chạy Bot**

```powershell
python V10_refactored.py
```

Nếu thành công, bạn sẽ thấy:
```
✅ Bot initialized for Admin: YOUR_ID
✅ Bot Started. ID: YOUR_ID
🟢 SYSTEM ONLINE
🟢 System monitor started
```

### **5️⃣ Test Telegram**

Gửi `/menu 1` hoặc `/start` từ Telegram → Bot sẽ gửi menu

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
V10/
├── .env (NEW)
├── config.py (NEW)
├── utils.py (NEW)
├── grabber.py (NEW - optimized)
├── media.py (NEW)
├── monitor.py (NEW)
├── V10_refactored.py (NEW - main bot)
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
```powershell
# Check .env tồn tại
Test-Path .env
# Check format đúng
Get-Content .env
```

**❌ Bot không connect**
```powershell
# Verify token
python -c "from config import API_TOKEN; print(API_TOKEN[:20] + '...')"
```

---

## **NEXT STEPS**

1. ✅ Cài .env + modules
2. ✅ Chạy V10_refactored.py
3. ✅ Test lệnh `/menu` trên Telegram
4. 📝 Xem `OPTIMIZATION_GUIDE.md` cho config nâng cao
5. 🔨 Build EXE: `pyinstaller --onefile --noconsole V10_refactored.py`

---

**🎉 XONG! Bot tối ưu đã sẵn sàng!**
