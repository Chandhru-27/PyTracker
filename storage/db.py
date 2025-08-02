import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
from storage import schema
from logs.db_logger import logger
import atexit

class Database:
    """
    Inside the Database class establish connection and other utilities
    """
    def __init__(self):
        """
        Establish connection to the local database file.
        """
        try:
            self.connection = sqlite3.connect("storage/User_db" , check_same_thread=False)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.connection.cursor()
            logger.debug("Connected to SQLite database")
        except Exception as e:
            logger.exception("Failed to connect to SQLite database")
    
# --------------------------- TABLE CREATION --------------------------------- #
    def create_general_user_stats(self):
        """
        Create user table for general stats.
        """
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_USER_STATS)
                logger.debug("User stats table created successfully.")
        except Exception as e:
            logger.exception("Failed to create GENERAL_USAGE table.")
    
    def create_appwise_usage(self):
        """
        Create user table for appwise stats.
        """
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_APPLICATION_USAGE)
                logger.debug("App-wise usage table created successfully.")
        except Exception as e:
            logger.exception("Failed to create APP_USAGE table.")
    
    def create_blocked_apps(self):
        """
        Create table to store blocked apps.
        """
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_BLOCKED_APPS)
                logger.debug("Blocked apps table created successfully.")
        except Exception as e:
            logger.exception("Failed to create blocked apps tabble.")

    def create_blocked_urls(self):
        """
        Create table to store blocked urls.
        """
        try:
            with self.connection:
                self.cursor.execute(schema.CREATE_TABLE_BLOCKED_URLS)
                logger.debug("Blocked urls table created successfully.")
        except Exception as e:
            logger.exception("Failed to create blocked urls tabble.")

# --------------------------- INSERTION & DELETION --------------------------------- # 
    def insert_current_usertime_info(self , date , screen_time , break_time):
        """
        Insert usertime information into general usage table.
        """
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
        """
        Insert appwise usertime info, if not available then update into appwise stat table.
        """
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

    def insert_blocked_app(self, app_name: str) -> None:
        app_name = app_name.strip().lower()
        try:
            with self.connection:
                if not self.is_app_blocked(app_name):
                    self.cursor.execute(
                        "INSERT INTO blocked_apps (app_name) VALUES (?)",
                        (app_name,)
                    )
                    logger.debug(f"Inserted {app_name} into blocked_apps.")
                else:
                    logger.debug(f"{app_name} already in blocked_apps.")
        except Exception as e:
            logger.exception(f"Failed to insert {app_name} into blocked apps.")

    def insert_blocked_url(self , url : str) -> None:
        url = url.strip().lower()
        try:
            with self.connection:
                if not self.is_url_blocked(url):
                    self.cursor.execute(
                        "INSERT INTO blocked_urls (url) VALUES (?)",
                        (url,)
                    )
                    logger.debug(f"Inserted {url} into blocked_urls.")
                else:
                    logger.debug(f"{url} already in blocked_urls.")
        except Exception as e:
            logger.exception(f"Failed to insert {url} into blockd urls.")

    def remove_from_blocked_apps(self, app_name: str) -> None:
        app_name = app_name.strip().lower()
        try:
            with self.connection:
                if self.is_app_blocked(app_name):
                    self.cursor.execute(
                        "DELETE FROM blocked_apps WHERE app_name = ?",
                        (app_name,)
                    )
                    logger.debug(f"Removed {app_name} from blocked_apps.")
                else:
                    logger.debug(f"{app_name} not found in blocked_apps.")
        except Exception as e:
            logger.exception(f"Failed to remove {app_name} from blocked_apps.")

    def remove_from_blocked_url(self , url : str) -> None:
        url = url.strip().lower()
        try:
            with self.connection:
                if self.is_url_blocked(url):
                    self.cursor.execute(
                        "DELETE FROM blocked_urls WHERE url = ?",
                        (url,)
                    )
                    logger.debug(f"Removed {url} from blocked_urls.")
                else:
                    logger.debug(f"{url} not found in blocked_urls.")
        except Exception as e:
            logger.exception(f"Failed to remove {url} from blocked_urls.")

# -------------------------- HELPER FUNCTIONS ----------------------- #
    def get_user_stat_id(self , date : str) -> int:
        """
        Get the foregin key ID to track appwise usage per day as user_stat_id.
        """
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
        """
        Get the foregin key ID to track appwise usage per day as user_stat_id.
        """
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
        """
        Load existing data to the variables for every re-start of the application.
        """
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
    
    def load_blocked_apps(self):
        try:
            with self.connection:
                self.cursor.execute("SELECT app_name FROM blocked_apps")
                result = self.cursor.fetchall()
                return set(app_name[0] for app_name in result)
        except Exception as e:
            logger.exception("Failed to load existing blocked apps.")
            return set()

    def load_blocked_urls(self):
        try:
            with self.connection:
                self.cursor.execute("""
                    SELECT url FROM blocked_urls
                """)
                result = self.cursor.fetchall()
                return set(url[0] for url in result)
        except Exception as e:
            logger.exception("Failed to load existing blocked urls.")
            return set()
    
    def is_app_blocked(self, app_name: str) -> bool:
        try:
            with self.connection:
                self.cursor.execute(
                    "SELECT 1 FROM blocked_apps WHERE app_name = ? LIMIT 1", 
                    (app_name,)
                )
                return self.cursor.fetchone() is not None
        except Exception as e:
            logger.exception(f"Failed to check if {app_name} is already blocked.")
            return False
        
    def is_url_blocked(self , url : str) -> None:
        try:
            with self.connection:
                self.cursor.execute(
                    "SELECT 1 FROM blocked_urls WHERE url = ? LIMIT 1", 
                    (url,)
                )
                return self.cursor.fetchone() is not None
        except Exception as e:
            logger.exception(f"Failed to check if {url} is already blocked.")
            return False


# --------------------- CLOSE CONNECTION ------------------------------ # 
    def close_connection(self):
        """
        Close cursor and connection to the database.
        """
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