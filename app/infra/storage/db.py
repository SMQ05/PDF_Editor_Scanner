"""
SQLite Database Manager for PDF Scanner App.
Thread-safe database operations.
"""
import sqlite3
import threading
from typing import Optional, List, Any
from contextlib import contextmanager
from kivy.logger import Logger


class DatabaseManager:
    """Thread-safe SQLite database manager."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """Get a database cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            Logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute a query and return lastrowid for inserts."""
        with self._lock:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[tuple]):
        """Execute a query with multiple parameter sets."""
        with self._lock:
            with self.get_cursor() as cursor:
                cursor.executemany(query, params_list)
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        with self._lock:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows."""
        with self._lock:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def initialize(self):
        """Create database tables if they don't exist."""
        with self._lock:
            with self.get_cursor() as cursor:
                # Documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        file_path TEXT,
                        thumbnail_path TEXT,
                        page_count INTEGER DEFAULT 0,
                        file_size INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Pages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        page_order INTEGER DEFAULT 0,
                        image_path TEXT,
                        thumbnail_path TEXT,
                        filter_applied TEXT DEFAULT 'original',
                        quad_points TEXT,
                        rotation INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                ''')
                
                # Scan sessions table (for process death recovery)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scan_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_data TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        is_complete INTEGER DEFAULT 0,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # App state table (ads, purchases, settings)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_state (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        ads_enabled INTEGER DEFAULT 1,
                        ads_removed_purchased INTEGER DEFAULT 0,
                        last_interstitial_time TEXT,
                        interstitial_count_today INTEGER DEFAULT 0,
                        last_count_reset_date TEXT,
                        max_pages_per_document INTEGER DEFAULT 200,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_documents_created 
                    ON documents(created_at DESC)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pages_document 
                    ON pages(document_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sessions_incomplete 
                    ON scan_sessions(is_complete)
                ''')
                
        Logger.info("Database: Tables initialized")
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            Logger.info("Database: Connection closed")
