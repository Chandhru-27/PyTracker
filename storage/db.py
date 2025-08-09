from contextlib import contextmanager
from utils.utilities import Utility
from logs.db_logger import logger
from storage import schema
import sqlite3
import time

DB_PATH = r"C:\Dev\PyTracker\storage\User_db"
TIMEOUT = 10          
MAX_RETRIES = 5       
RETRY_DELAY = 0.2     

class Database:
    """Class handles database CRUD logic and thread safety by WAL mode protection."""
    _wal_set = False 
    _tables_created = False

    def __init__(self):
        """Initialize database connection settings."""
        try:
            if not Database._wal_set:
                self._set_wal_mode_once()
                Database._wal_set = True
                logger.debug("SQLite ready (WAL mode, FK enabled).")

            if not Database._tables_created:
                self._ensure_tables_exist()
                Database._tables_created = True

        except Exception as e:
            logger.exception(f"DB init failed: {e}")

    def _ensure_tables_exist(self):
        """Ensure all required tables exist, creating them if necessary."""
        required_tables = {
            'GENERAL_USAGE': schema.CREATE_TABLE_USER_STATS,
            'APP_USAGE': schema.CREATE_TABLE_APPLICATION_USAGE,
            'blocked_apps': schema.CREATE_TABLE_BLOCKED_APPS,
            'blocked_urls': schema.CREATE_TABLE_BLOCKED_URLS
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                with self.get_connection() as (conn, cursor):
                    # Check which tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    existing_tables = {row[0] for row in cursor.fetchall()}
                    
                    # Create missing tables
                    for table_name, create_sql in required_tables.items():
                        if table_name not in existing_tables:
                            logger.info(f"Creating missing table: {table_name}")
                            cursor.execute(create_sql)
                    
                    conn.commit()
                return
                
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.debug(f"Table check locked, retry {attempt+1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise
                    
        raise sqlite3.OperationalError("Failed to verify tables after retries.")
    
    def _set_wal_mode_once(self):
        """Set WAL mode with retry to avoid lock issues."""
        for attempt in range(MAX_RETRIES):
            try:
                conn = sqlite3.connect(DB_PATH, timeout=TIMEOUT, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.close()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.debug(f"WAL setup locked, retry {attempt+1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise
        raise sqlite3.OperationalError("Failed to set WAL mode after retries.")

    @contextmanager
    def get_connection(self):
        """Fresh connection per operation (thread-safe)."""
        conn = sqlite3.connect(DB_PATH, timeout=TIMEOUT, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn, conn.cursor()
            conn.commit()
        finally:
            conn.close()

    def execute_with_retry(self, query, params=()):
        """Run a write query with retry on lock."""
        for attempt in range(MAX_RETRIES):
            try:
                with self.get_connection() as (conn, cursor):
                    cursor.execute(query, params)
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.debug(f"DB locked, retry {attempt+1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise
        raise sqlite3.OperationalError("DB still locked after retries.")

    def fetch_one(self, query, params=()):
        """Custom fetchone function to pass along the query."""
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=()):
        """Custom fetchall function to pass along the query."""
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return cursor.fetchall()

    # ---------- Table creation ----------
    def create_general_user_stats(self):
        """Function creates the general usage table."""
        self.execute_with_retry(schema.CREATE_TABLE_USER_STATS)
        logger.debug("Table GENERAL_USAGE ready.")

    def create_appwise_usage(self):
        """Functuon creates the app usage table."""
        self.execute_with_retry(schema.CREATE_TABLE_APPLICATION_USAGE)
        logger.debug("Table APP_USAGE ready.")

    def create_blocked_apps(self):
        """Function creates the blocked app table."""
        self.execute_with_retry(schema.CREATE_TABLE_BLOCKED_APPS)
        logger.debug("Table BLOCKED_APPS ready.")

    def create_blocked_urls(self):
        """Function creates the blocked urls table."""
        self.execute_with_retry(schema.CREATE_TABLE_BLOCKED_URLS)
        logger.debug("Table BLOCKED_URLS ready.")

    # ---------- Insert / Update ----------

    def insert_blocked_app(self, app_name: str):
        """Handles db logic to block apps."""
        self.execute_with_retry(
            "INSERT OR IGNORE INTO blocked_apps (app_name) VALUES (?)",
            (app_name.strip().lower(),)
        )
        logger.debug(f"Blocked app added: {app_name}")

    def insert_blocked_url(self, url: str):
        """Handles db logic to block urls."""
        self.execute_with_retry(
            "INSERT OR IGNORE INTO blocked_urls (url) VALUES (?)",
            (url.strip().lower(),)
        )
        logger.debug(f"Blocked URL added: {url}")

    def remove_from_blocked_apps(self, app_name: str):
        """Handles db logic to unblock apps."""
        self.execute_with_retry(
            "DELETE FROM blocked_apps WHERE app_name = ?",
            (app_name.strip().lower(),)
        )
        logger.debug(f"Blocked app removed: {app_name}")

    def remove_from_blocked_url(self, url: str):
        """Handles db logic to unblock urls."""
        self.execute_with_retry(
            "DELETE FROM blocked_urls WHERE url = ?",
            (url.strip().lower(),)
        )
        logger.debug(f"Blocked URL removed: {url}")

    def update_daily_state(self, date, screen_time, break_time, app_usage_dict):
        """
        Atomically update general usage and appwise usage in one transaction.
        Automatically handles date rollover by creating a new row with 0 values 
        if the current date is different from the latest entry in the DB.
        """
        for attempt in range(MAX_RETRIES):
            try:
                with self.get_connection() as (conn, cursor):
                    
                    cursor.execute("SELECT date FROM GENERAL_USAGE ORDER BY date DESC LIMIT 1")
                    last_row = cursor.fetchone()

                    if not last_row or last_row[0] != date:
                        cursor.execute("""
                            INSERT INTO GENERAL_USAGE (date, screen_time, break_time)
                            VALUES (?, 0, 0)
                            ON CONFLICT(date) DO NOTHING;
                        """, (date,))
                        conn.commit()

                    cursor.execute("""
                        INSERT INTO GENERAL_USAGE (date, screen_time, break_time)
                        VALUES (?, ?, ?)
                        ON CONFLICT(date)
                        DO UPDATE SET
                            screen_time = excluded.screen_time,
                            break_time = excluded.break_time;
                    """, (date, screen_time, break_time))

                    cursor.execute("SELECT id FROM GENERAL_USAGE WHERE date = ?", (date,))
                    result = cursor.fetchone()
                    if not result:
                        raise Exception("Failed to get user_stat_id after insert.")
                    user_stat_id = result[0]

                    for app, duration in app_usage_dict.items():
                        cursor.execute("""
                            INSERT INTO APP_USAGE (app_name, date, usage_duration, user_stat_id)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(app_name, date)
                            DO UPDATE SET usage_duration = excluded.usage_duration;
                        """, (app, date, duration, user_stat_id))

                return 

            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.debug(f"[TXN] DB locked, retry {attempt+1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        raise sqlite3.OperationalError("DB still locked after retries.")
        
    def reset_data(self, date):
        """Resets the user data for the current day (Backend logic of reset button in UI)."""
        try:
            with self.get_connection() as (conn , cursor):
                cursor.execute("DELETE FROM GENERAL_USAGE WHERE date = ?",(date))
                conn.commit()
                cursor.execute("DELETE FROM APP_USAGE WHERE date = ?",(date))
                conn.commit()
        except Exception as e:
            logger.debug(f"Unable to reset data for {date}")

    def run_cleanup(self):
        """Runs a quick db cleanup of unknown apps which might not be an actual executable"""
        try:
            with self.get_connection() as (conn , cursor):
                app = "unknow"
                cursor.execute("DELETE FROM APP_USAGE WHERE app_name = ?",(app,))
                conn.commit()
                logger.debug("Cleaned up database.")
        except Exception as e:
            print(e)
            logger.debug("Failed to run database cleanup.")
    
    # ---------- Helpers ----------
    
    def get_user_stat_id(self, date: str):
        """Returns the foreign key to map with app usage table."""
        result = self.fetch_one("SELECT id FROM GENERAL_USAGE WHERE date = ?", (date,))
        return result[0] if result else None
    
    def get_user_history(self):
        """Returns the complete user history for screen and breaktime."""
        result = self.fetch_all("""
            SELECT rnk, date, screen_time, break_time
            FROM (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY date desc) AS rnk,
                    date,
                    screen_time,
                    break_time
                FROM GENERAL_USAGE
            ) AS sub
        """)
        history = []
        for data in result:
            id = data[0]
            date = data[1]
            screen_time = Utility.get_formatted_screen_time(data[2])
            break_time = Utility.get_formatted_screen_time(data[3])
            history.append([id , date , screen_time , break_time]) 
        return history

    def load_existing_general_usage(self, date):
        """Returns the screen and breaktime stat of current day"""
        return self.fetch_one(
            "SELECT screen_time, break_time FROM GENERAL_USAGE WHERE date = ?",
            (date,)
        )
    
    def load_existing_appwise_usage(self, date):
        """Returns the app usage stat of current day."""
        data = self.fetch_all(
            "SELECT app_name, usage_duration FROM APP_USAGE WHERE date = ?",
            (date,)
        )
        return {app: duration for app, duration in data}
    
    def load_blocked_apps(self):
        """Returns the blocked apps to load into the in-memory variables."""
        return {row[0] for row in self.fetch_all("SELECT app_name FROM blocked_apps")}

    def load_blocked_urls(self):
        """Returns the blocked urls to load into the in-memory variables."""
        return {row[0] for row in self.fetch_all("SELECT url FROM blocked_urls")}

    def is_app_blocked(self, app_name: str) -> bool:
        """Checks if an app is already blocked."""
        return self.fetch_one(
            "SELECT 1 FROM blocked_apps WHERE app_name = ? LIMIT 1",
            (app_name,)
        ) is not None

    def is_url_blocked(self, url: str) -> bool:
        """Checks if an url is already blocked."""
        return self.fetch_one(
            "SELECT 1 FROM blocked_urls WHERE url = ? LIMIT 1",
            (url,)
        ) is not None
