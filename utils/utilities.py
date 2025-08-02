from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from logs.app_logger import logger
import win32process
import subprocess
import threading
import win32gui
import psutil
import ctypes
import time
import os

# -------------------------
# Utility Functions
# -------------------------

class Utility:
    audio_lock = threading.Lock()

    @staticmethod
    def get_idle_time():
        """
        Returns the idle time in seconds using Windows APIs.
        """
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0

    @staticmethod
    def get_active_window_title():
        """
        Returns the title of the currently focused window.
        """
        handle = win32gui.GetForegroundWindow()
        try:
            _,process_id = win32process.GetWindowThreadProcessId(handle)
            process_obj = psutil.Process(pid=process_id)
            return process_obj.name()
        except Exception:
            return 'Unknow'

    @staticmethod
    def get_active_audio_status():
        """
        Get the active audio status safely from a single thread.
        """
        with Utility.audio_lock:
            import comtypes
            from comtypes import CoInitialize, CoUninitialize
            try:
                # Initialize seperate thread for working with audio
                CoInitialize()
            except Exception:
                pass  # Already initialized

            try:
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    try:
                        volume = session.SimpleAudioVolume
                        if session.State == 1:  # Active audio
                            level = volume.GetMasterVolume()
                            if level > 0.0:
                                return True
                    except Exception:
                        continue
                return False
            finally:
                # Basic cleanup of initialized threads
                try:
                    CoUninitialize()
                except Exception:
                    pass

    @staticmethod
    def terminate_blocked_app(process_name, blocked_apps):
        """
        Terminates a process if it's in the blocked_apps list.
        """ 
        try:
            if process_name in blocked_apps:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == process_name:
                        proc.kill()
                logger.debug(f"Terminated blocked app {process_name}")
        except Exception as e:
            logger.debug(f"Failed to terminate blocked app {process_name}: {e}")

    @staticmethod
    def block_url(HOST_PATH, BLOCKED_DOMAINS):
        try:
            with open(HOST_PATH , 'r+') as file:
                file_data = file.read()
                for website in BLOCKED_DOMAINS:
                    if website not in file_data:
                        file.write(f"128.0.0.1 {website}\n")
        except Exception as e:
            print("Error opening file/Blocking website")
        
    
    # def unblock_url(self , HOST_PATH , BLOCKED_DOMAINS):
    #     self.clean_hosts_file(HOST_PATH , BLOCKED_DOMAINS)
    #     self.flush_dns()
    #     self.restart_dns_service()
    

    @staticmethod
    def clean_hosts_file(HOST_PATH: str, BLOCKED_DOMAINS: set):
        try:
            with open(HOST_PATH, 'r') as file:
                lines = file.readlines()

            # Filter lines that do NOT contain any blocked domain
            new_lines = [line for line in lines if not any(domain in line for domain in BLOCKED_DOMAINS)]

            with open(HOST_PATH, 'w') as file:
                file.writelines(new_lines)

            logger.debug("[+] Hosts file cleaned.")
        except PermissionError:
            logger.debug("[-] Permission denied: Run this script as administrator.")
            exit(1)
        except Exception as e:
            logger.debug(f"[-] Error cleaning hosts file: {e}")
            exit(1)

    @staticmethod
    def restart_dns_service():
        try:
            subprocess.run(["net", "stop", "dnscache"], check=True)
            subprocess.run(["net", "start", "dnscache"], check=True)
            logger.debug("[+] DNS Client service restarted.")
        except subprocess.CalledProcessError:
            logger.debug("[-] Could not restart DNS Client (might require reboot or higher privileges).")

    @staticmethod
    def flush_dns():
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True)
            logger.debug("[+] DNS cache flushed.")
        except subprocess.CalledProcessError as e:
            logger.debug(f"[-] Failed to flush DNS: {e}")

    @staticmethod
    def run_every(interval, func, *args, **kwargs):
        """
        Helper function to avoid time skips and still call the function with time intervals.
        """
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