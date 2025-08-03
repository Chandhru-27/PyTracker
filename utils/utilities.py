from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from logs.app_logger import logger
import win32process
import subprocess
import pythoncom
import threading
import win32gui
import psutil
import ctypes
import time
import wmi
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
    def kill_process_tree(pid):
        """
        Kills the given process and all its child processes.
        """
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            parent.kill()
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            logger.debug(f"Access denied for PID {pid} - try running as admin.")

    @staticmethod
    def background_scanner(blocked_apps: set, scan_interval: int = 5):
        """
        Continuously scans for blocked apps and kills them if found.
        """
        while True:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() in blocked_apps:
                        logger.debug(f"[SCAN] Blocking {proc.info['name']} (PID: {proc.info['pid']})")
                        Utility.kill_process_tree(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(scan_interval)

    @staticmethod
    def wmi_event_watcher(blocked_apps: set):
        """Blocks new processes instantly when they are created."""
        pythoncom.CoInitialize()
        try:
            while True:
                try:
                    c = wmi.WMI()
                    watcher = c.Win32_Process.watch_for("creation")
                    logger.debug("[WMI] Connected to process creation watcher")

                    while True:
                        try:
                            new_proc = watcher()
                            if new_proc.Caption and new_proc.Caption.lower() in blocked_apps:
                                logger.debug(f"[EVENT] Blocking {new_proc.Caption} (PID: {new_proc.ProcessId})")
                                Utility.kill_process_tree(new_proc.ProcessId)
                        except wmi.x_wmi as e:
                            logger.debug(f"[WMI] Watcher error, reconnecting: {e}")
                            break  # Exit inner loop to reconnect

                except Exception as e:
                    logger.debug(f"[WMI] Connection error: {e}")
                    time.sleep(5)  # Wait before retry
        finally:
            pythoncom.CoUninitialize()


    @staticmethod
    def start_app_blocker(blocked_apps: set, scan_interval: int = 5):
        """Starts both background scanning and event watching."""
        if not blocked_apps:
            return  # Nothing to block

        t1 = threading.Thread(target=Utility.background_scanner, args=(blocked_apps, scan_interval), daemon=True)
        t2 = threading.Thread(target=Utility.wmi_event_watcher, args=(blocked_apps,), daemon=True)
        t1.start()
        t2.start()

        logger.debug(f"App blocker started for: {', '.join(blocked_apps)}")

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
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

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