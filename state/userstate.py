import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from utils.utilities import Utility
from logs.app_logger import logger
from utils import keywords
import threading

class UserActivityState:
    """Mutable in-memory state for tracking user activity, app usage, and timers."""
    def __init__(self):
        self.idle_time = 0
        self.active_window = ""
        self.screen_time = 0
        self.break_start_time = None
        self.total_break_duration = 0
        self.total_stretch_time = 0
        self.is_active_audio = False
        self.last_check = datetime.now()
        self.last_date = self.last_check.date()  
        self.lock = threading.Lock()
        self.screentime_per_app = {}
        self.blocked_apps = set()
        self.blocked_urls = set()
        self.is_paused = False

    def update(self):
        """Update activity metrics based on idle time, active window, and audio status.
        Edge-case handling:
        - Respect pause: when paused, do not mutate timers or accumulate breaks
        - Day rollover: reset counters safely
        - Break timing: accumulate break duration incrementally while idle
        - Clamp elapsed to sane bounds to avoid large jumps on clock changes
        - Avoid counting unknown window names in per-app map
        """
        with self.lock:
            now = datetime.now()
            today = now.date()

            if self.screen_time > 86400: 
                logger.warning("Screen time exceeded 24 hours, resetting to zero.")
                self.screen_time = 0
            if self.total_break_duration > 86400: 
                logger.warning("Total break duration exceeded 24 hours, resetting to zero.")
                self.total_break_duration = 0
            
            if today != self.last_date:
                self.reset_daily_counters()
                self.last_date = today
                logger.debug("Day rollover detect and handled properly.")

            if self.is_paused:
                self.last_check = now
                return

            process_name = Utility.get_active_window_title()
            window = os.path.splitext(process_name)[0].lower() if process_name else ""
            audio = Utility.get_active_audio_status()

            elapsed = (now - self.last_check).total_seconds()

            if elapsed < 0:
                elapsed = 0
            elif elapsed > 5:
                logger.warning(f"Large elapsed time detected: {elapsed:.2f}s, clamping to 5s")
                elapsed = 5

            self.idle_time = Utility.get_idle_time()
            self.active_window = window
            self.is_active_audio = audio

            audio_app = self.active_window.lower()
            is_video_playback = any(kw in audio_app for kw in keywords.video_keywords)

            is_active_user = (self.idle_time < 60) or (is_video_playback and self.is_active_audio)

            if is_active_user:
                if self.break_start_time is not None:
                    self.break_start_time = None
                self.screen_time += elapsed
                self.total_stretch_time += elapsed
                if window and window != "unknow":
                    self.screentime_per_app[window] = self.screentime_per_app.get(window, 0) + elapsed
            else:
                if not is_video_playback and self.idle_time >= 60:
                    if self.break_start_time is None:
                        logger.debug(f"total screen time: {self.get_formatted_screen_time(self.screen_time)}")
                        logger.debug("user is idle — starting break timer")
                        self.break_start_time = now
                    else:
                        self.total_break_duration += elapsed

        self.last_check = now

    def reset_daily_counters(self):
        """Reset daily counters when a new day is detected."""
        logger.info("New day detected — resetting daily counters")
        self.screen_time = 0
        self.total_break_duration = 0
        self.total_stretch_time = 0
        self.screentime_per_app.clear()
        self.break_start_time = None


    def get_formatted_screen_time(self, arg):
        """Convert duration in seconds to HH:MM:SS string."""
        return str(timedelta(seconds=int(arg)))

    def load_existing_data(self, screen_time, break_time, app_usage, blocked_apps, blocked_urls):
        """Load persisted session metrics and lists into the current state."""
        self.screen_time = screen_time
        self.total_break_duration = break_time
        self.screentime_per_app.update(app_usage)
        self.blocked_apps = blocked_apps
        self.blocked_urls =blocked_urls
