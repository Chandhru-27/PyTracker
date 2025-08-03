from datetime import datetime, timedelta
from utils.utilities import Utility
from state.userstate import UserActivityState
from logs.app_logger import logger
from utils import keywords
from storage import db
import atexit

# ------------------------
# Initialize the Database 
# ------------------------
user_db = db.Database()
user_db.create_general_user_stats()
user_db.create_appwise_usage()

# ------------------------
# Activity Tracker Logic
# ------------------------
def activity_tracker(state: UserActivityState):
    """
    Tracks basic activities like screentime, breaktime and appwise screentimes.
    """
    def activity_logic():
        state.update()
        with state.lock:
            date = datetime.now().strftime("%Y-%m-%d")
            screen_time = state.screen_time
            break_time = state.total_break_duration     
            user_db.insert_current_usertime_info(date=date, screen_time=screen_time, break_time=break_time)
            
            for app, duration in state.screentime_per_app.items():
                user_stat_id = user_db.get_user_stat_id(date=date)
                user_db.upsert_appwise_usertime_info(date, app, duration, user_stat_id)
                
    Utility.run_every(5, activity_logic)

# ------------------------
# Reminder Logic
# ------------------------
def reminder_logic(state: UserActivityState):
    """
    Holds the mathematical logic of how breaktime is assumed and accounted.
    """
    reminder_threshold = 45 * 60  # 45 minutes
    idle_threshold = 60  # seconds of inactivity to count as break

    def main_logic():
        nonlocal reminder_threshold, idle_threshold
        with state.lock:
            # Check for 45-minute reminder
            if state.total_stretch_time >= reminder_threshold:
                logger.debug("Reminder: You've been working for 45 minutes. Time to take a break!")
                state.total_stretch_time = 0  # Reset stretch timer

            # Detect break start (if not video playback)
            audio_app = state.active_window.lower()
            is_video_playback = any(kw in audio_app for kw in keywords.video_keywords)
            
            if state.idle_time >= idle_threshold and not (is_video_playback and state.is_active_audio):
                if state.break_start_time is None:
                    state.break_start_time = datetime.now() - timedelta(seconds=state.idle_time)

            # Detect return from break
            elif state.break_start_time is not None:
                break_end_time = datetime.now() - timedelta(seconds=state.idle_time)
                break_duration = (break_end_time - state.break_start_time).total_seconds()

                state.total_break_duration += break_duration
                logger.debug(f"Break Ended. Duration: {state.get_formatted_screen_time(break_duration)}")
                logger.debug(f"Total Break Time: {state.get_formatted_screen_time(state.total_break_duration)}")
                state.break_start_time = None

    Utility.run_every(5, main_logic)
