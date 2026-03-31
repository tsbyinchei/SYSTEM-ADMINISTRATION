"""
Watchdog Module
Monitors the main bot process and restarts it if it dies.
Runs as a separate lightweight process.

Developer: TsByin
Version: 12.0
"""

import os
import sys
import time
import logging
import subprocess
import platform
from pathlib import Path

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

# When frozen: both watchdog and main are .exe in the same directory.
# When running as .py: keep them side by side.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    MAIN_NAME = "SystemCheck.exe"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MAIN_NAME = "V12.py"

MAIN_PATH = os.path.join(BASE_DIR, MAIN_NAME)
RESTART_DELAY = 3        # seconds to wait before restarting
MAX_RESTARTS = 20        # guard against infinite crash loop
RESTART_WINDOW = 120     # seconds — reset counter after this much uptime
LOG_FILE = os.path.join(BASE_DIR, "watchdog.log")
EXIT_REASON_FILE = os.path.join(BASE_DIR, '.exit_reason')  # Exit reason marker

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def launch_main() -> subprocess.Popen:
    """Start the main bot process and return the Popen handle."""
    if getattr(sys, 'frozen', False):
        cmd = [MAIN_PATH]
    else:
        cmd = [sys.executable, MAIN_PATH]

    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
    )
    logger.info(f"Started main process PID={proc.pid}: {' '.join(cmd)}")
    return proc


def register_watchdog_autostart():
    """Add watchdog itself to Windows Task Scheduler (AtLogon, hidden)."""
    try:
        if platform.system() != "Windows":
            return

        if getattr(sys, 'frozen', False):
            wd_exe = sys.executable          # watchdog.exe
        else:
            # Running as .py — use pythonw.exe for silent startup
            wd_exe = None
            python_dir = os.path.dirname(sys.executable)
            pythonw = os.path.join(python_dir, "pythonw.exe")
            this_file = os.path.abspath(__file__)
            if os.path.exists(pythonw):
                wd_exe = f'"{pythonw}" "{this_file}"'
            else:
                wd_exe = f'"{sys.executable}" "{this_file}"'

        task_name = "SystemHealthMonitor"

        xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2"
  xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>System Health Monitor Service</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT10S</Delay>
    </LogonTrigger>
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
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{wd_exe if getattr(sys, 'frozen', False) else sys.executable}</Command>
      {'<Arguments>' + os.path.abspath(__file__) + '</Arguments>' if not getattr(sys, 'frozen', False) else ''}
      <WorkingDirectory>{BASE_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

        xml_path = os.path.join(BASE_DIR, "_wd_task.xml")
        with open(xml_path, "w", encoding="utf-16") as f:
            f.write(xml)

        subprocess.run(
            ["schtasks", "/create", "/tn", task_name,
             "/xml", xml_path, "/f"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
            check=False,
        )
        os.remove(xml_path)
        logger.info(f"Task Scheduler entry registered: {task_name}")
    except Exception as e:
        logger.warning(f"register_watchdog_autostart failed: {e}")


def _read_exit_reason():
    """Read and clear exit reason marker written by main process."""
    try:
        import json
        if not os.path.exists(EXIT_REASON_FILE):
            return "unknown"
        with open(EXIT_REASON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            os.remove(EXIT_REASON_FILE)
        except Exception:
            pass
        reason = str(data.get("reason", "unknown"))
        return reason or "unknown"
    except Exception as e:
        logger.warning(f"Failed to read exit reason: {e}")
        return "unknown"


# ------------------------------------------------------------------
# Main watchdog loop
# ------------------------------------------------------------------

def run():
    logger.info("=== Watchdog started ===")

    if not os.path.exists(MAIN_PATH):
        logger.error(f"Main target not found: {MAIN_PATH}")
        sys.exit(1)

    # Register auto-start once
    register_watchdog_autostart()

    restart_count = 0
    proc = launch_main()
    start_time = time.time()

    while True:
        ret = proc.wait()   # blocks until process exits
        uptime = time.time() - start_time
        reason = _read_exit_reason()

        if reason == "manual_stop":
            logger.info(
                f"Main process exited by manual stop (code={ret}, uptime={uptime:.0f}s). "
                "Watchdog will exit without restart."
            )
            break

        # Reset restart counter if it ran healthily for a while
        if uptime > RESTART_WINDOW:
            restart_count = 0

        restart_count += 1
        logger.warning(
            f"Main process exited (code={ret}, reason={reason}, uptime={uptime:.0f}s). "
            f"Restart #{restart_count}/{MAX_RESTARTS}"
        )

        if restart_count > MAX_RESTARTS:
            logger.error("Too many restarts in a short window — giving up to avoid loop.")
            time.sleep(60)
            restart_count = 0   # try again after cooldown

        time.sleep(RESTART_DELAY)
        proc = launch_main()
        start_time = time.time()


if __name__ == "__main__":
    run()

# ════════════════════════════════════════════════
# Developer: TsByin
# Module: Watchdog — Auto-restart main bot process
# ════════════════════════════════════════════════
