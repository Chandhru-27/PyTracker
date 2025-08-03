import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime , timedelta
from utils.utilities import Utility
from logs.app_logger import logger
from utils import keywords
import threading
import os

# -------------------------------
# Shared State - Class Definition
# -------------------------------

class UserActivityState:
    """
    Manages and maintains the current state of the user's activity including screen time,
    idle status, app usage, break tracking, and app blocking.
    """
    def __init__(self):
        self.idle_time = 0
        self.active_window = ""
        self.screen_time = 0
        self.break_start_time = None
        self.total_break_duration = 0
        self.total_stretch_time = 0
        self.is_active_audio = False
        self.last_check = datetime.now()
        self.lock = threading.Lock()
        self.screentime_per_app = {}
        self.blocked_apps = {}
        self.blocked_urls = set()

    def update(self):
        """
        Updates the current state of user activity:
        - Checks idle time and active window
        - Determines whether the user is active (based on movement or video/audio activity)
        - Tracks screen time and break time
        - Kills blocked applications
        """
        with self.lock:
            now = datetime.now() # Get the current date
            process_name = Utility.get_active_window_title() # Get the current process name as ".exe"
            window = os.path.splitext(process_name)[0].lower() # Split and clean the name for db usage
            audio = Utility.get_active_audio_status() # Check if audio is running in the background
            
            elapsed = (now - self.last_check).total_seconds() # Calculate elapsed time
            # Store the output values to class objects
            self.idle_time = Utility.get_idle_time() 
            self.active_window = window
            self.is_active_audio = audio

            # Get audio and video playback status
            audio_app = self.active_window.lower()
            is_video_playback = any(kw in audio_app for kw in keywords.video_keywords)

            # User is considered active if:
            # 1. Not idle (idle_time < 60), OR
            # 2. Watching video with audio playing
            is_active_user = (self.idle_time < 60) or (is_video_playback and self.is_active_audio)

            # Calculate the values
            if is_active_user:
                self.screen_time += elapsed
                self.total_stretch_time += elapsed
                self.screentime_per_app[window] = self.screentime_per_app.get(window, 0) + elapsed
            else:
            # Only count as break time if not video playback
                if not is_video_playback and self.idle_time >= 60:
                    if self.break_start_time is None:
                        logger.debug(f"total screen time: {self.get_formatted_screen_time(self.screen_time)}")
                        logger.debug(f"user is idle")
                        self.break_start_time = now

        self.last_check = now

    def get_formatted_screen_time(self, arg):
        """
        Converts total screen time in seconds to HH:MM:SS format.
        """
        return str(timedelta(seconds=int(arg)))

    def load_existing_data(self, screen_time, break_time, app_usage , blocked_apps , blocked_urls):
        """
        Loads previously stored session data to continue tracking.
        """
        self.screen_time = screen_time
        self.total_break_duration = break_time
        self.screentime_per_app.update(app_usage)
        self.blocked_apps = blocked_apps
        self.blocked_urls =blocked_urls
