import subprocess
import sys
import os

def trigger_script_at_startup():
    file_path = os.path.abspath('app.py')
    python_path = sys.executable
    task_name = "PymonitorTrigger"
    task_command = f'"{python_path} {file_path}"'

    command = [
        "schtasks",
        "/Create",
        "/TN", task_name,
        "/TR", task_command,
        "/SC", "ONLOGON",
        "/RL", "HIGHEST",
        "/F"
    ]

    subprocess.run(command , shell=True)

trigger_script_at_startup()
