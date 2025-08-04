from datetime import datetime, timedelta
from utils.utilities import Utility
from state.userstate import UserActivityState
from frontend_ui import notification
from logs.app_logger import logger
from utils.utilities import shutdown_event
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
        try:
            if shutdown_event.is_set():
                return

            state.update()
            with state.lock:
                date = datetime.now().strftime("%Y-%m-%d")
                app_data = state.screentime_per_app.copy()
                screen = state.screen_time
                brk = state.total_break_duration

            user_db.update_daily_state(
                date=date,
                screen_time=screen,
                break_time=brk,
                app_usage_dict=app_data
            )

        except Exception as e:
            logger.exception("Crash in activity_logic:")
                
    Utility.run_every(5, activity_logic)

# ------------------------
# Reminder Logic
# ------------------------
def reminder_logic(state: UserActivityState):
    """
    Holds the mathematical logic of how breaktime is assumed and accounted.
    """
    if not shutdown_event.is_set():
        reminder_threshold = 2 * 60  # 45 minutes
        idle_threshold = 60  # seconds of inactivity to count as break

        def main_logic():
            try:
                nonlocal reminder_threshold, idle_threshold
                with state.lock:
                    # Check for 45-minute reminder
                    if state.total_stretch_time >= reminder_threshold:
                        if Utility.is_notification_disabled() or Utility.is_focus_assist_on():
                            notification.customnotify()
                        notification.notify()
                        state.total_stretch_time = 0

                    audio_app = state.active_window.lower()
                    is_video_playback = any(kw in audio_app for kw in keywords.video_keywords)

                    if state.idle_time >= idle_threshold and not (is_video_playback and state.is_active_audio):
                        if state.break_start_time is None:
                            state.break_start_time = datetime.now() - timedelta(seconds=state.idle_time)

                    elif state.break_start_time is not None:
                        break_end_time = datetime.now() - timedelta(seconds=state.idle_time)
                        break_duration = (break_end_time - state.break_start_time).total_seconds()
                        state.total_break_duration += break_duration
                        logger.debug(f"Break Ended. Duration: {state.get_formatted_screen_time(break_duration)}")
                        logger.debug(f"Total Break Time: {state.get_formatted_screen_time(state.total_break_duration)}")
                        state.break_start_time = None
            except Exception as e:
                logger.exception("Crash in reminder_logic:")

    Utility.run_every(5, main_logic)
