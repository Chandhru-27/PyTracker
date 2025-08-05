import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
from utils.utilities import Utility

conn = sqlite3.connect(r"C:\Dev\PyTracker\storage\User_db")
cursor = conn.cursor()
cursor.execute("""
    SELECT rnk, date, screen_time, break_time
    FROM (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY date) AS rnk,
            date,
            screen_time,
            break_time
        FROM GENERAL_USAGE
    ) AS sub
""")

result = cursor.fetchall()
history = []
for data in result:
    id = data[0]
    date = data[1]
    screen_time = Utility.get_formatted_screen_time(data[2])
    break_time = Utility.get_formatted_screen_time(data[3])
    history.append([id , date , screen_time , break_time])
print(history)

