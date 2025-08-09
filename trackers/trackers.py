from state.userstate import UserActivityState
from utils.utilities import shutdown_event
from frontend_ui import notification
from utils.utilities import Utility
from logs.app_logger import logger
from datetime import datetime
from utils import keywords
from storage import db

# ====== Initialize the Database ======= #

user_db = db.Database()
user_db.create_general_user_stats()
user_db.create_appwise_usage()

# ====== Activity Tracker Logic ======= #

def activity_tracker(state: UserActivityState):
    """Track screen/break time and appwise usage, persisting periodic snapshots to the DB."""
    def activity_logic(gap_seconds = 0):
        try:
            if shutdown_event.is_set():
                return

            if state.is_paused:
                logger.warning("Tracker Paused")
                return
            
            state.update()
            logger.debug("ACTIVITY THREAD IS RUNNING.")
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
                
    Utility.run_precise_timer(2, activity_logic)


# ===== Reminder Logic ======= #

def reminder_logic(state: UserActivityState):
    """Compute break detection over time, handling idle/sleep gaps and merging short active periods."""
    if not shutdown_event.is_set():
        reminder_threshold = 45 * 60 
        idle_threshold = 60  
        break_merge_gap = 15  

        def main_logic(gap_seconds=0):
            try:
                if state.is_paused:
                    return
                
                nonlocal reminder_threshold, idle_threshold, break_merge_gap

                with state.lock:
                    now = datetime.now()
                    logger.debug("REMINDER THREAD IS RUNNING.")
                    if gap_seconds > idle_threshold:
                        state.total_break_duration += gap_seconds
                        logger.debug(
                            f"Break recorded due to sleep/inactivity gap: {gap_seconds:.0f}s"
                        )
                        return 

                    if state.total_stretch_time >= reminder_threshold:
                        if Utility.is_notification_disabled() or Utility.is_focus_assist_on():
                            notification.customnotify()
                        notification.notify()
                        state.total_stretch_time = 0

                    is_video_playback = any(
                        kw in state.active_window.lower() for kw in keywords.video_keywords
                    )
                    is_sleeping = (
                        state.active_window.lower() in ("unknown", "unknow")
                    )
                    is_user_idle = (state.idle_time >= idle_threshold)

                    valid_break = (is_sleeping or is_user_idle)

                    if valid_break:
                        if state.break_start_time is None:
                            state.break_start_time = now
                            logger.debug(
                                f"Break Started. Reason: {'Sleep' if is_sleeping else 'Idle'}"
                            )

                    elif state.break_start_time is not None:
                        break_end_time = now
                        break_duration = (break_end_time - state.break_start_time).total_seconds()

                        if hasattr(state, "last_break_end_time") and state.last_break_end_time:
                            time_since_last_break = (
                                break_end_time - state.last_break_end_time
                            ).total_seconds()
                            if time_since_last_break <= break_merge_gap:
                                logger.debug("Merging with previous break.")
                                break_duration += getattr(state, "last_break_duration", 0)

                        state.total_break_duration += break_duration
                        state.last_break_end_time = break_end_time
                        state.last_break_duration = break_duration

                        logger.debug(
                            f"Break Ended. Duration: {state.get_formatted_screen_time(break_duration)}"
                        )
                        logger.debug(
                            f"Total Break Time: {state.get_formatted_screen_time(state.total_break_duration)}"
                        )

                        state.break_start_time = None

            except Exception:
                logger.exception("Crash in reminder_logic:")

        Utility.run_precise_timer(1, main_logic)
