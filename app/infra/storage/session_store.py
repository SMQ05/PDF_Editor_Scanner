"""
Session Store for PDF Scanner App.
Persists scan sessions across process death.
"""
import json
from typing import Optional
from datetime import datetime
from kivy.logger import Logger

from app.domain.models import ScanSession
from .db import DatabaseManager


class SessionStore:
    """Manages persistence of scan sessions for process death recovery."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_session(self, session: ScanSession) -> int:
        """Save or update a scan session. Returns session ID."""
        now = datetime.now().isoformat()
        session_data = json.dumps(session.to_dict())
        
        try:
            if session.id:
                # Update existing
                self.db.execute('''
                    UPDATE scan_sessions SET
                        session_data = ?, is_complete = ?, updated_at = ?
                    WHERE id = ?
                ''', (session_data, 1 if session.is_complete else 0, now, session.id))
                return session.id
            else:
                # Insert new
                session_id = self.db.execute('''
                    INSERT INTO scan_sessions 
                    (session_data, started_at, is_complete, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    session_data,
                    session.started_at.isoformat(),
                    1 if session.is_complete else 0,
                    now
                ))
                session.id = session_id
                Logger.info(f"SessionStore: Created new session {session_id}")
                return session_id
        except Exception as e:
            Logger.error(f"SessionStore: Save failed: {e}")
            return -1
    
    def get_active_session(self) -> Optional[ScanSession]:
        """Get the most recent incomplete session."""
        try:
            row = self.db.fetch_one('''
                SELECT * FROM scan_sessions 
                WHERE is_complete = 0 
                ORDER BY updated_at DESC 
                LIMIT 1
            ''')
            
            if row:
                session_data = json.loads(row['session_data'])
                session = ScanSession.from_dict(session_data)
                session.id = row['id']
                Logger.info(f"SessionStore: Restored session {session.id} with {len(session.pages)} pages")
                return session
        except Exception as e:
            Logger.error(f"SessionStore: Get active session failed: {e}")
        
        return None
    
    def get_session(self, session_id: int) -> Optional[ScanSession]:
        """Get a specific session by ID."""
        try:
            row = self.db.fetch_one(
                'SELECT * FROM scan_sessions WHERE id = ?', (session_id,)
            )
            
            if row:
                session_data = json.loads(row['session_data'])
                session = ScanSession.from_dict(session_data)
                session.id = row['id']
                return session
        except Exception as e:
            Logger.error(f"SessionStore: Get session failed: {e}")
        
        return None
    
    def delete_session(self, session_id: int) -> bool:
        """Delete a session by ID."""
        try:
            self.db.execute('DELETE FROM scan_sessions WHERE id = ?', (session_id,))
            Logger.info(f"SessionStore: Deleted session {session_id}")
            return True
        except Exception as e:
            Logger.error(f"SessionStore: Delete failed: {e}")
            return False
    
    def mark_complete(self, session_id: int) -> bool:
        """Mark a session as complete."""
        try:
            now = datetime.now().isoformat()
            self.db.execute('''
                UPDATE scan_sessions SET is_complete = 1, updated_at = ?
                WHERE id = ?
            ''', (now, session_id))
            Logger.info(f"SessionStore: Marked session {session_id} as complete")
            return True
        except Exception as e:
            Logger.error(f"SessionStore: Mark complete failed: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Delete completed sessions older than specified days. Returns count deleted."""
        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Count first
            row = self.db.fetch_one('''
                SELECT COUNT(*) as count FROM scan_sessions 
                WHERE is_complete = 1 AND updated_at < ?
            ''', (cutoff,))
            count = row['count'] if row else 0
            
            # Delete
            self.db.execute('''
                DELETE FROM scan_sessions 
                WHERE is_complete = 1 AND updated_at < ?
            ''', (cutoff,))
            
            Logger.info(f"SessionStore: Cleaned up {count} old sessions")
            return count
        except Exception as e:
            Logger.error(f"SessionStore: Cleanup failed: {e}")
            return 0
