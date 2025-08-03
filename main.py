from state.userstate import UserActivityState
from datetime import datetime , timedelta
from utils.utilities import Utility
from frontend_ui import tst
from logs.app_logger import logger
from trackers import trackers
from storage import db
import threading
import ctypes
import time
import sys
import os

def thread_monitor():
    while True:
        active_threads = threading.active_count()
        print("\n[THREAD MONITOR] Active threads:", active_threads)
        for t in threading.enumerate():
            print(f"  - Name: {t.name}, Daemon: {t.daemon}")
        time.sleep(5)  # check every 5 seconds

# -------------------------
# Main Launcher
# ------------------------- 

if __name__ == "__main__":
    # Run as admin if not already
    # if not Utility.is_admin():
    #     ctypes.windll.shell32.ShellExecuteW(
    #         None, "runas", sys.executable, " ".join(sys.argv), None, 1
    #     )
    #     logger.debug("Running as admin")

    # Initialize the database and activity state
    user_db = db.Database()
    state = UserActivityState()

    # Load previously stored data (if available)
    today = datetime.now().strftime("%Y-%m-%d")
    existing = user_db.load_existing_general_usage(date=today)

    if existing:
        screen_time, break_time = existing
        blocked_apps = user_db.load_blocked_apps()
        blocked_urls = user_db.load_blocked_urls()
        app_usage = user_db.load_existing_appwise_usage(today)
        state.load_existing_data(screen_time, break_time, app_usage , blocked_apps , blocked_urls)
        logger.debug(f"Loaded previous usage: Screen Time: {screen_time}, Break Time: {break_time}")
        user_db.remove_from_blocked_apps("chrome.exe")
        Utility.start_app_blocker(state.blocked_apps, scan_interval=1)
        # Print count of active threads

        if state.blocked_apps:
            logger.debug(state.blocked_apps)
        if state.blocked_urls:
            logger.debug(state.blocked_urls)
    else:
        logger.debug("No previous usage found. Starting fresh.")
        if state.blocked_apps:
            Utility.start_app_blocker(state.blocked_apps, scan_interval=1)


    # Start background threads for tracking and reminders
    tracker_thread = threading.Thread(target=trackers.activity_tracker, args=(state,), daemon=True)
    reminder_thread = threading.Thread(target=trackers.reminder_logic, args=(state,), daemon=True)


    # Start the threads
    tracker_thread.start()
    reminder_thread.start()
  
    tst.start_ui(state)
