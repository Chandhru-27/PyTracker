import sqlite3
from storage import schema
from logs.db_logger import logger
import atexit
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Database:
    def __init__(self):
        try:
            self.connection = sqlite3.connect("storage/User_db" , check_same_thread=False)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.connection.cursor()
            logger.debug("Connected to SQLite database")
        except Exception as e:
            logger.exception("Failed to connect to SQLite database")
    
    def create_general_user_stats(self):
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_USER_STATS)
                logger.debug("User stats table created successfully.")
        except Exception as e:
            logger.exception("Failed to create GENERAL_USAGE table.")
    
    def create_appwise_usage(self):
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_APPLICATION_USAGE)
                logger.debug("App-wise usage table created successfully.")
        except Exception as e:
            logger.exception("Failed to create APP_USAGE table.")
    
    def insert_current_usertime_info(self , date , screen_time , break_time):
        try:
            with self.connection:
                self.cursor.execute("""
                INSERT INTO GENERAL_USAGE (date , screen_time , break_time)
                values (?, ?, ?) 
                ON CONFLICT(date)
                DO UPDATE SET
                    screen_time = excluded.screen_time,
                    break_time = excluded.break_time;                             
                """,(date , screen_time , break_time))
                logger.debug(f"Inserted stats for {date} - Screen Time: {screen_time}, Break Time: {break_time}")
        except Exception as e:
            logger.exception("Failed to insert into GENERAL_USAGE.")

    def upsert_appwise_usertime_info(self, date, app_name, duration, user_stat_id):
        try:
            with self.connection:
                self.cursor.execute("""
                    INSERT INTO APP_USAGE (app_name, date, usage_duration, user_stat_id)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(app_name, date)
                    DO UPDATE SET usage_duration = excluded.usage_duration;
                """, (app_name, date, duration, user_stat_id))
                logger.debug(f"Upserted usage for app '{app_name}': +{duration}s on {date}")
        except Exception as e:
            logger.exception("Failed to upsert app-wise usage data.")

    def get_user_stat_id(self , date) -> int:
        try:
            with self.connection:
                self.cursor.execute(""" SELECT id FROM GENERAL_USAGE WHERE date = ?""",(date,))
                result = self.cursor.fetchone()
                if result:
                    user_stat_id = result[0]
                    logger.debug(f"User stat id fetched as {user_stat_id}")
                    return user_stat_id
                else:
                    logger.debug("No entry found for the given date.")
                    return None
        except Exception as e:
            logger.exception("Failed to fetch user_stat_id")
            return None
    
    def load_existing_general_usage(self , date):
        try:
            with self.connection:
                self.cursor.execute("""
                SELECT screen_time, break_time FROM GENERAL_USAGE WHERE date = ?
            """, (date,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.exception("Failed to load existing usage data.")
            return None

    def load_existing_appwise_usage(self , date):
        try:
            with self.connection:
                self.cursor.execute("""
                    SELECT app_name, usage_duration FROM APP_USAGE WHERE date = ?
                """, (date,))
                result = self.cursor.fetchall()
                return {app: duration for app, duration in result}
        except Exception as e:
            logger.exception("Failed to load app-wise usage data.")
            return {}

    def close_connection(self):
        try:
            if self.cursor:
                self.cursor.close()
                logger.debug("Database cursor closed.")
            if self.connection:
                self.connection.close()
                logger.debug("Database connection closed.")
        except Exception as e:
            logger.exception("Error while closing database resources.")


if __name__ == "__main__":
    user_db = Database()
    atexit.register(user_db.close_connection)