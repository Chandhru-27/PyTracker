import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from threading import Thread
from state.userstate import UserActivityState
from storage.db import Database
from trackers import trackers
from utils.utilities import Utility
from logs.app_logger import logger
from datetime import datetime

# ----------------------------
# Initialize DB and load data
# ----------------------------
user_db = Database()
user_db.create_blocked_apps()
user_db.create_blocked_urls()

HOST_PATH = r"C:\Windows\System32\drivers\etc\hosts"
today = datetime.now().strftime("%Y-%m-%d")
existing = user_db.load_existing_general_usage(date=today)

state = UserActivityState()
if existing:
    screen_time, break_time = existing
    blocked_apps = user_db.load_blocked_apps()
    blocked_urls = user_db.load_blocked_urls()
    app_usage = user_db.load_existing_appwise_usage(today)
    state.load_existing_data(screen_time, break_time, app_usage, blocked_apps, blocked_urls)

    logger.debug(f"Loaded previous usage: Screen Time: {screen_time}, Break Time: {break_time}")
    logger.debug("Loaded existing blocked apps." if state.blocked_apps else "No previously blocked apps found, Starting fresh.")
    logger.debug("Loaded existing blocked urls." if state.blocked_urls else "No previously blocked urls found, Starting fresh.")
else:
    logger.debug("No previous usage found. Starting fresh.")

# ----------------------------
# UI Callback Functions
# ----------------------------
def add_app():
    app = app_entry.get().strip().lower()
    if app:
        if app not in state.blocked_apps:
            with state.lock:
                state.blocked_apps.add(app)
                user_db.insert_blocked_app(app_name=app)
            status_label.config(text=f"✅ Blocked App: {app}")
        else:
            status_label.config(text=f"⚠️ '{app}' is already blocked.")
        app_entry.delete(0, tk.END)
    else:
        status_label.config(text="⚠️ Please enter a valid app name.")

def remove_app():
    app = app_entry.get().strip().lower()
    if app in state.blocked_apps:
        with state.lock:
            state.blocked_apps.discard(app)
            user_db.remove_from_blocked_apps(app_name=app)
        status_label.config(text=f"❌ Unblocked App: {app}")
        app_entry.delete(0, tk.END)
    else:
        status_label.config(text=f"⚠️ App '{app}' not in blocklist")

def add_url():
    try:
        url = url_entry.get().strip()
        if url:
            with state.lock:
                state.blocked_urls.add(url)
                Utility.block_url(HOST_PATH=HOST_PATH, BLOCKED_DOMAINS=state.blocked_urls)
                user_db.insert_blocked_url(url=url)
            status_label.config(text=f"✅ Blocked URL: {url}")
            url_entry.delete(0, tk.END)
        else:
            status_label.config(text="⚠️ Please enter a valid URL.")
    except Exception as e:
        status_label.config(text=f"❌ Error: {e}")

def remove_url():
    try:
        url = url_entry.get().strip()
        if url in state.blocked_urls:
            with state.lock:
                Utility.clean_hosts_file(HOST_PATH=HOST_PATH, BLOCKED_DOMAINS=state.blocked_urls)
                state.blocked_urls.discard(url)
                user_db.remove_from_blocked_url(url=url)
                Utility.flush_dns()
                Utility.restart_dns_service()
            status_label.config(text=f"❌ Unblocked URL: {url}")
            url_entry.delete(0, tk.END)
        else:
            status_label.config(text=f"⚠️ URL '{url}' not in blocklist")
    except Exception as e:
        status_label.config(text=f"❌ Error: {e}")

# ----------------------------
# Tkinter UI Setup
# ----------------------------
root = tk.Tk()
root.title("App & URL Blocker")
root.geometry("400x300")
root.resizable(False, False)

# App controls
tk.Label(root, text="App (.exe name):").pack(pady=(10, 0))
app_entry = tk.Entry(root, width=40)
app_entry.pack()

tk.Button(root, text="Block App", command=add_app).pack(pady=2)
tk.Button(root, text="Unblock App", command=remove_app).pack()

# URL controls
tk.Label(root, text="URL (e.g., www.youtube.com):").pack(pady=(15, 0))
url_entry = tk.Entry(root, width=40)
url_entry.pack()

tk.Button(root, text="Block URL", command=add_url).pack(pady=2)
tk.Button(root, text="Unblock URL", command=remove_url).pack()

# Status label
status_label = tk.Label(root, text="", fg="blue")
status_label.pack(pady=10)

# ----------------------------
# Background Threads
# ----------------------------
Thread(target=trackers.activity_tracker, args=(state,), daemon=True).start()
Thread(target=trackers.reminder_logic, args=(state,), daemon=True).start()

root.mainloop()  # Tkinter must run in main thread