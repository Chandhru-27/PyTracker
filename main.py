from state.userstate import UserActivityState
from datetime import datetime , timedelta
from logs.app_logger import logger
from trackers import trackers
from storage import db
import threading
import os

# -------------------------
# Main Launcher
# ------------------------- 

if __name__ == "__main__":
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
        if state.blocked_apps:
            logger.debug(state.blocked_apps)
        if state.blocked_urls:
            logger.debug(state.blocked_urls)
    else:
        logger.debug("No previous usage found. Starting fresh.")

    # Start background threads for tracking and reminders
    tracker_thread = threading.Thread(target=trackers.activity_tracker, args=(state,))
    reminder_thread = threading.Thread(target=trackers.reminder_logic, args=(state,))

    # Start the threads
    tracker_thread.start()
    reminder_thread.start()

    # Join the threads
    tracker_thread.join()
    reminder_thread.join()
