from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from logs.app_logger import logger
import win32process
import win32gui
import psutil
import ctypes
import time
import os

# -------------------------
# Utility Functions
# -------------------------


def get_idle_time():
    """Returns the idle time in seconds using Windows APIs."""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def get_active_window_title():
    """Returns the title of the currently focused window."""
    handle = win32gui.GetForegroundWindow()
    try:
        _,process_id = win32process.GetWindowThreadProcessId(handle)
        process_obj = psutil.Process(pid=process_id)
        return process_obj.name()
    except Exception:
        return 'Unknow'

def get_active_audio_status():
    import comtypes
    from comtypes import CoInitialize, CoUninitialize
    try:
        CoInitialize()
    except Exception:
        pass  # Already initialized

    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            try:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                if session.State == 1:  # ACTIVE
                    level = volume.GetMasterVolume()
                    if level > 0.0:
                        return True
            except Exception:
                continue
        return False
    finally:
        try:
            CoUninitialize()
        except Exception:
            pass


def run_every(interval, func, *args, **kwargs):
    next_time = time.time()
    while True:
        func(*args, **kwargs)
        next_time += interval
        sleep_time = next_time - time.time()
        process = psutil.Process(os.getpid())
        logger.debug(f"Memory Usage: {process.memory_info().rss / 1024 ** 2:.2f} MB")
        logger.debug(f"CPU Usage: {process.cpu_percent(interval=1)}%")
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # If delayed too much, resync to current time
            next_time = time.time()