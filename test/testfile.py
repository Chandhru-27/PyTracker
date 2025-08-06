import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
from utils.utilities import Utility

conn = sqlite3.connect(r"C:\Dev\PyTracker\storage\User_db")
cursor = conn.cursor()
cursor.execute("SELECT app_name FROM blocked_apps")

result = cursor.fetchall()
history = []
for row in result:
    history.append(row[0])

print(history)
# import winreg

# def get_installed_apps():
#     apps = set()
#     reg_paths = [
#         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
#         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
#     ]

#     for reg_path in reg_paths:
#         try:
#             reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
#             for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
#                 sub_key_name = winreg.EnumKey(reg_key, i)
#                 sub_key = winreg.OpenKey(reg_key, sub_key_name)
#                 try:
#                     app_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
#                     apps.add(app_name)
#                 except FileNotFoundError:
#                     continue
#         except Exception:
#             continue

#     return sorted(apps)

# print(get_installed_apps())