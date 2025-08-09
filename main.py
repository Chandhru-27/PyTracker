from frontend_ui.base_layout import TimeTrackerApp
from state.userstate import UserActivityState
from datetime import datetime , timedelta
from utils.utilities import Utility
from logs.app_logger import logger
from frontend_ui import interface
from trackers import trackers
from frontend_ui import tst
from storage import db
import threading
import ctypes
import time
import sys
import os

 
if __name__ == "__main__":

    if not Utility.is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        logger.debug("Running as admin")

    user_db = db.Database()
    state = UserActivityState()

    today = datetime.now().strftime("%Y-%m-%d")
    existing = user_db.load_existing_general_usage(date=today)

    blocked_apps = user_db.load_blocked_apps()
    blocked_urls = user_db.load_blocked_urls()
    state.blocked_apps = blocked_apps
    state.blocked_urls = blocked_urls

    if existing:
        screen_time, break_time = existing
        app_usage = user_db.load_existing_appwise_usage(today)
        state.load_existing_data(screen_time, break_time, app_usage, blocked_apps, blocked_urls)
        logger.debug(f"Loaded previous usage: Screen Time: {screen_time}, Break Time: {break_time}")
    else:
        logger.debug("No previous usage found. Starting fresh.")

    if state.blocked_apps:
        Utility.start_app_blocker(state.blocked_apps, scan_interval=1)

    tracker_thread = threading.Thread(target=trackers.activity_tracker, args=(state,), daemon=True)
    reminder_thread = threading.Thread(target=trackers.reminder_logic, args=(state,), daemon=True)

    tracker_thread.start()
    reminder_thread.start()
  
    app = TimeTrackerApp(state=state)
    app.tracker_thread = tracker_thread
    app.reminder_thread = reminder_thread
    app.mainloop()
    # interface.start_ui(shared_state=state)
