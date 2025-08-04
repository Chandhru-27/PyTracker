import sys
import os
import sqlite3
import time
from storage import schema
from logs.db_logger import logger
import atexit
from contextlib import contextmanager

DB_PATH = "storage/User_db"
TIMEOUT = 10          # Seconds to wait for a locked DB
MAX_RETRIES = 5       # Retry attempts on lock
RETRY_DELAY = 0.2     # Seconds between retries


class Database:
    _wal_set = False  # Class-level flag so WAL mode is enabled only once

    def __init__(self):
        """Initialize database connection settings."""
        try:
            if not Database._wal_set:
                self._set_wal_mode_once()
                Database._wal_set = True
                logger.debug("SQLite ready (WAL mode, FK enabled).")
        except Exception as e:
            logger.exception(f"DB init failed: {e}")

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
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=()):
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params)
            return cursor.fetchall()

    # ---------- Table creation ----------
    def create_general_user_stats(self):
        self.execute_with_retry(schema.CREATE_TABLE_USER_STATS)
        logger.debug("Table GENERAL_USAGE ready.")

    def create_appwise_usage(self):
        self.execute_with_retry(schema.CREATE_TABLE_APPLICATION_USAGE)
        logger.debug("Table APP_USAGE ready.")

    def create_blocked_apps(self):
        self.execute_with_retry(schema.CREATE_TABLE_BLOCKED_APPS)
        logger.debug("Table BLOCKED_APPS ready.")

    def create_blocked_urls(self):
        self.execute_with_retry(schema.CREATE_TABLE_BLOCKED_URLS)
        logger.debug("Table BLOCKED_URLS ready.")

    # ---------- Insert / Update ----------

    def insert_blocked_app(self, app_name: str):
        self.execute_with_retry(
            "INSERT OR IGNORE INTO blocked_apps (app_name) VALUES (?)",
            (app_name.strip().lower(),)
        )
        logger.debug(f"Blocked app added: {app_name}")

    def insert_blocked_url(self, url: str):
        self.execute_with_retry(
            "INSERT OR IGNORE INTO blocked_urls (url) VALUES (?)",
            (url.strip().lower(),)
        )
        logger.debug(f"Blocked URL added: {url}")

    def remove_from_blocked_apps(self, app_name: str):
        self.execute_with_retry(
            "DELETE FROM blocked_apps WHERE app_name = ?",
            (app_name.strip().lower(),)
        )
        logger.debug(f"Blocked app removed: {app_name}")

    def remove_from_blocked_url(self, url: str):
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
                    
                    # Check latest date in DB
                    cursor.execute("SELECT date FROM GENERAL_USAGE ORDER BY date DESC LIMIT 1")
                    last_row = cursor.fetchone()

                    if not last_row or last_row[0] != date:
                        # New day detected → insert fresh zeroed row
                        cursor.execute("""
                            INSERT INTO GENERAL_USAGE (date, screen_time, break_time)
                            VALUES (?, 0, 0)
                            ON CONFLICT(date) DO NOTHING;
                        """, (date,))
                        conn.commit()

                    # Insert/update today's general usage
                    cursor.execute("""
                        INSERT INTO GENERAL_USAGE (date, screen_time, break_time)
                        VALUES (?, ?, ?)
                        ON CONFLICT(date)
                        DO UPDATE SET
                            screen_time = excluded.screen_time,
                            break_time = excluded.break_time;
                    """, (date, screen_time, break_time))

                    # Get user_stat_id for today's row
                    cursor.execute("SELECT id FROM GENERAL_USAGE WHERE date = ?", (date,))
                    result = cursor.fetchone()
                    if not result:
                        raise Exception("Failed to get user_stat_id after insert.")
                    user_stat_id = result[0]

                    # Insert/update app-wise usage for today
                    for app, duration in app_usage_dict.items():
                        cursor.execute("""
                            INSERT INTO APP_USAGE (app_name, date, usage_duration, user_stat_id)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(app_name, date)
                            DO UPDATE SET usage_duration = excluded.usage_duration;
                        """, (app, date, duration, user_stat_id))

                return  # success

            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.debug(f"[TXN] DB locked, retry {attempt+1}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        raise sqlite3.OperationalError("DB still locked after retries.")

    # ---------- Helpers ----------
    def get_user_stat_id(self, date: str):
        result = self.fetch_one("SELECT id FROM GENERAL_USAGE WHERE date = ?", (date,))
        return result[0] if result else None
    
    
    def load_existing_general_usage(self, date):
        return self.fetch_one(
            "SELECT screen_time, break_time FROM GENERAL_USAGE WHERE date = ?",
            (date,)
        )

    def load_existing_appwise_usage(self, date):
        data = self.fetch_all(
            "SELECT app_name, usage_duration FROM APP_USAGE WHERE date = ?",
            (date,)
        )
        return {app: duration for app, duration in data}
    
    def load_blocked_apps(self):
        return {row[0] for row in self.fetch_all("SELECT app_name FROM blocked_apps")}

    def load_blocked_urls(self):
        return {row[0] for row in self.fetch_all("SELECT url FROM blocked_urls")}

    def is_app_blocked(self, app_name: str) -> bool:
        return self.fetch_one(
            "SELECT 1 FROM blocked_apps WHERE app_name = ? LIMIT 1",
            (app_name,)
        ) is not None

    def is_url_blocked(self, url: str) -> bool:
        return self.fetch_one(
            "SELECT 1 FROM blocked_urls WHERE url = ? LIMIT 1",
            (url,)
        ) is not None

    def close_connection(self):
        """No persistent connection to close in this design."""
        logger.debug("No persistent DB connection to close.")


if __name__ == "__main__":
    user_db = Database()
    atexit.register(user_db.close_connection)
