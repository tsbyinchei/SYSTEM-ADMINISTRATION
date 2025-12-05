# 📦 BUILD EXE - HƯỚNG DẪN CHI TIẾT

> **Developer:** TsByin  
> **Version:** 2.0 (EXE Build Guide)

## **CHUẨN BỊ**

### **1. Cài PyInstaller**

```powershell
pip install pyinstaller
```

### **2. Chuẩn Bị .env File**

Đảm bảo `.env` có tất cả config:

```bash
API_TOKEN=YOUR_TOKEN
ADMIN_ID=YOUR_ID
MONITOR_INTERVAL=1
CPU_ALERT_THRESHOLD=95
# ... others
```

### **3. Tạo Icon (Optional)**

```powershell
# Nếu có icon (icon.ico)
# Nếu không, bỏ qua --icon parameter
```

---

## **BUILD OPTIONS**

### **Option 1: Basic (Simplest)**

```powershell
pyinstaller --onefile --noconsole V10_refactored.py
```

**Output:**
- `dist/V10_refactored.exe` (~150MB)
- Chạy ở background (no console)
- Single file

### **Option 2: With Admin Rights**

```powershell
pyinstaller --onefile --noconsole --uac-admin V10_refactored.py
```

**Thêm:**
- Admin privilege (cần cho blocking features)
- UAC prompt on first run

### **Option 3: With Icon**

```powershell
pyinstaller --onefile --noconsole --icon=icon.ico V10_refactored.py
```

**Thêm:**
- Custom icon in taskbar & file properties

### **Option 4: Production (RECOMMENDED)**

```powershell
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico ^
    --name=SystemCheck ^
    --distpath=.\release ^
    --specpath=.\build ^
    --buildpath=.\build\temp ^
    V10_refactored.py
```

**Features:**
- ✅ All above features
- ✅ Custom name: `SystemCheck.exe`
- ✅ Organized output directory
- ✅ Clean build artifacts

### **Option 5: With Hidden Imports (If module errors)**

```powershell
pyinstaller --onefile --noconsole --uac-admin ^
    --hidden-import=config ^
    --hidden-import=utils ^
    --hidden-import=grabber ^
    --hidden-import=media ^
    --hidden-import=monitor ^
    V10_refactored.py
```

**Use if:** PyInstaller can't auto-detect imports

---

## **RECOMMENDED BUILD COMMAND**

```powershell
# Production build
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico ^
    --name=SystemCheck ^
    --distpath=.\release ^
    --buildpath=.\build ^
    --specpath=.\build ^
    V10_refactored.py

# Verify
ls .\release\
# Should see: SystemCheck.exe
```

---

## **POST-BUILD STEPS**

### **1. Copy .env to release**

```powershell
Copy-Item .env .\release\.env
```

**Important:** EXE needs .env in same directory!

### **2. Test Locally**

```powershell
cd .\release
.\SystemCheck.exe

# Check logs
Get-Content bot.log -Tail 10
```

### **3. Verify Features**

From Telegram:
- [ ] Send `/start` → Menu appears
- [ ] Send `/menu 1` → ReplyKeyboard
- [ ] Send `/menu 2` → InlineKeyboard
- [ ] Test `/stats` → Shows stats
- [ ] Test screenshot command
- [ ] Check `bot.log` for errors

### **4. Optional: Create Installer**

Use NSIS or Inno Setup:

```powershell
# Install Inno Setup, then create script:
# installer.iss
[Setup]
AppName=System Monitor V10
AppVersion=1.0
DefaultDirName={pf}\SystemMonitor
DefaultGroupName=System Monitor
OutputDir=.\installer
OutputBaseFilename=SystemMonitor_Setup

[Files]
Source: "release\SystemCheck.exe"; DestDir: "{app}"
Source: ".env"; DestDir: "{app}"

[Run]
Filename: "{app}\SystemCheck.exe"; Flags: nowait postinstall
```

---

## **BUILD STATISTICS**

### **File Size Comparison**

```
V10_refactored.py       ≈  25 KB (source)
SystemCheck.exe        ≈ 150 MB (compiled)
  ├─ Python runtime   ≈  80 MB
  ├─ Libraries        ≈  60 MB
  ├─ Our modules      ≈  10 MB
  └─ Assets           ≈   1 MB
```

### **Compression (Optional)**

```powershell
# UPX compression (needs install first)
pip install upx
upx .\release\SystemCheck.exe --best

# Result: 150MB → ~50MB (2-3x smaller)
```

---

## **TROUBLESHOOTING BUILD**

### **Problem: "ModuleNotFoundError: No module named 'config'"**

**Solution:**
```powershell
pyinstaller --onefile --noconsole ^
    --hidden-import=config ^
    --hidden-import=utils ^
    --hidden-import=grabber ^
    --hidden-import=media ^
    --hidden-import=monitor ^
    V10_refactored.py
```

### **Problem: "No such file or directory: '.env'"**

**Solution:**
```powershell
# Copy .env to release folder
Copy-Item .env .\release\.env
```

### **Problem: "Access Denied" when running EXE**

**Solution:**
1. Run as Administrator
2. Add to Windows Defender exclusions
3. Or: Disable Windows Defender temporarily during setup

### **Problem: EXE is very large (500+ MB)**

**Solution:**
1. Use UPX compression
2. Or use `--onedir` (creates folder instead of file)

```powershell
pyinstaller --onedir --noconsole --uac-admin V10_refactored.py
```

---

## **DISTRIBUTION CHECKLIST**

- [x] EXE file created
- [x] .env file copied to release
- [x] Test EXE locally with .env
- [x] Verify all features work
- [x] Check logs for errors
- [x] Create version tag
- [x] Sign EXE (optional but recommended)

---

## **CODE SIGNING (Optional - Avoid SmartScreen)**

### **Create Self-Signed Certificate:**

```powershell
# Run as Administrator

# 1. Create certificate
$cert = New-SelfSignedCertificate -DnsName "SystemMonitor" ^
    -CertStoreLocation "Cert:\CurrentUser\My" ^
    -Type CodeSigningCert

# 2. Export for trusted store
Export-Certificate -Cert $cert -FilePath "Cert.cer"

# 3. Trust it
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store(
    [System.Security.Cryptography.X509Certificates.StoreName]::Root, "CurrentUser")
$rootStore.Open("ReadWrite")
$rootStore.Add($cert)
$rootStore.Close()

# 4. Sign EXE
Set-AuthenticodeSignature -Certificate $cert -FilePath ".\release\SystemCheck.exe"

# 5. Verify signature
Get-AuthenticodeSignature ".\release\SystemCheck.exe"
```

**Benefits:**
- Removes "Unknown Publisher" warning
- Reduces SmartScreen warnings
- Shows your app name on install

---

## **DEPLOYMENT OPTIONS**

### **Option A: Direct EXE Distribution**

```powershell
# Share .exe + .env
Zip-File -SourcePath ".\release\*" -DestPath "SystemMonitor.zip"
```

**Pros:** Simple, single file
**Cons:** Requires manual .env setup

### **Option B: With Setup Script**

Create `setup.bat`:

```batch
@echo off
echo Installing System Monitor...

REM Download or copy .env
echo Configure .env:
pause

REM Run EXE
echo Starting bot...
SystemCheck.exe

pause
```

### **Option C: MSI Installer**

Use WiX Toolset for professional installer

---

## **QUICK START AFTER BUILD**

1. **Copy files:**
   ```powershell
   Copy-Item .env .\release\.env
   ```

2. **Test:**
   ```powershell
   cd .\release
   .\SystemCheck.exe
   ```

3. **Verify:**
   ```powershell
   Get-Content bot.log -Tail 20
   ```

4. **Deploy:**
   ```powershell
   # Zip for distribution
   Compress-Archive -Path .\release -DestinationPath SystemMonitor.zip
   ```

---

## **FINAL NOTES**

✅ **Single File:** Use `--onefile`  
✅ **Background Mode:** Use `--noconsole`  
✅ **Admin Privilege:** Use `--uac-admin`  
✅ **Custom Name:** Use `--name=YourName`  
✅ **Icon:** Use `--icon=path/to/icon.ico`  

**Remember:** Always include `.env` file with EXE!

---

**Build successful? 🎉 Your bot is ready to deploy!**
