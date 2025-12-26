"""
Data Repositories for PDF Scanner App.
CRUD operations for domain entities.
"""
import json
from typing import List, Optional
from datetime import datetime
from kivy.logger import Logger

from app.domain.models import Document, Page, AppState, FilterType
from .db import DatabaseManager


class DocumentRepository:
    """Repository for Document entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_document(self, document: Document) -> int:
        """Save or update a document. Returns document ID."""
        now = datetime.now().isoformat()
        
        if document.id:
            # Update existing
            self.db.execute('''
                UPDATE documents SET
                    name = ?, file_path = ?, thumbnail_path = ?,
                    page_count = ?, file_size = ?, updated_at = ?
                WHERE id = ?
            ''', (
                document.name, document.file_path, document.thumbnail_path,
                document.page_count, document.file_size, now, document.id
            ))
            return document.id
        else:
            # Insert new
            doc_id = self.db.execute('''
                INSERT INTO documents 
                (name, file_path, thumbnail_path, page_count, file_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document.name, document.file_path, document.thumbnail_path,
                document.page_count, document.file_size, now, now
            ))
            document.id = doc_id
            return doc_id
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """Get a document by ID."""
        row = self.db.fetch_one(
            'SELECT * FROM documents WHERE id = ?', (doc_id,)
        )
        if row:
            return self._row_to_document(row)
        return None
    
    def get_all_documents(self, limit: int = 50, offset: int = 0) -> List[Document]:
        """Get all documents ordered by creation date."""
        rows = self.db.fetch_all('''
            SELECT * FROM documents 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [self._row_to_document(row) for row in rows]
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete a document by ID."""
        try:
            self.db.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
            return True
        except Exception as e:
            Logger.error(f"DocumentRepository: Delete failed: {e}")
            return False
    
    def rename_document(self, doc_id: int, new_name: str) -> bool:
        """Rename a document."""
        try:
            now = datetime.now().isoformat()
            self.db.execute(
                'UPDATE documents SET name = ?, updated_at = ? WHERE id = ?',
                (new_name, now, doc_id)
            )
            return True
        except Exception as e:
            Logger.error(f"DocumentRepository: Rename failed: {e}")
            return False
    
    def _row_to_document(self, row) -> Document:
        """Convert database row to Document object."""
        return Document(
            id=row['id'],
            name=row['name'],
            file_path=row['file_path'] or '',
            thumbnail_path=row['thumbnail_path'] or '',
            page_count=row['page_count'] or 0,
            file_size=row['file_size'] or 0,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
        )


class PageRepository:
    """Repository for Page entity operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_page(self, page: Page) -> int:
        """Save or update a page. Returns page ID."""
        now = datetime.now().isoformat()
        quad_str = str(page.quad_points) if page.quad_points else None
        
        if page.id:
            # Update existing
            self.db.execute('''
                UPDATE pages SET
                    document_id = ?, page_order = ?, image_path = ?,
                    thumbnail_path = ?, filter_applied = ?, quad_points = ?,
                    rotation = ?
                WHERE id = ?
            ''', (
                page.document_id, page.order, page.image_path,
                page.thumbnail_path, page.filter_applied.value,
                quad_str, page.rotation, page.id
            ))
            return page.id
        else:
            # Insert new
            page_id = self.db.execute('''
                INSERT INTO pages 
                (document_id, page_order, image_path, thumbnail_path, 
                 filter_applied, quad_points, rotation, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                page.document_id, page.order, page.image_path,
                page.thumbnail_path, page.filter_applied.value,
                quad_str, page.rotation, now
            ))
            page.id = page_id
            return page_id
    
    def get_pages_for_document(self, doc_id: int) -> List[Page]:
        """Get all pages for a document."""
        rows = self.db.fetch_all('''
            SELECT * FROM pages WHERE document_id = ? ORDER BY page_order
        ''', (doc_id,))
        return [self._row_to_page(row) for row in rows]
    
    def delete_pages_for_document(self, doc_id: int) -> bool:
        """Delete all pages for a document."""
        try:
            self.db.execute('DELETE FROM pages WHERE document_id = ?', (doc_id,))
            return True
        except Exception as e:
            Logger.error(f"PageRepository: Delete failed: {e}")
            return False
    
    def _row_to_page(self, row) -> Page:
        """Convert database row to Page object."""
        quad_points = None
        if row['quad_points']:
            try:
                quad_points = eval(row['quad_points'])
            except:
                pass
        
        return Page(
            id=row['id'],
            document_id=row['document_id'],
            order=row['page_order'],
            image_path=row['image_path'] or '',
            thumbnail_path=row['thumbnail_path'] or '',
            filter_applied=FilterType(row['filter_applied'] or 'original'),
            quad_points=quad_points,
            rotation=row['rotation'] or 0,
            created_at=datetime.fromisoformat(row['created_at']),
        )


class AppStateRepository:
    """Repository for application state (ads, purchases)."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_app_state(self) -> Optional[AppState]:
        """Get the current app state."""
        row = self.db.fetch_one('SELECT * FROM app_state WHERE id = 1')
        if row:
            return self._row_to_state(row)
        return None
    
    def save_app_state(self, state: AppState) -> bool:
        """Save or update the app state."""
        now = datetime.now().isoformat()
        last_interstitial = state.last_interstitial_time.isoformat() if state.last_interstitial_time else None
        
        try:
            # Try update first
            row = self.db.fetch_one('SELECT id FROM app_state WHERE id = 1')
            
            if row:
                self.db.execute('''
                    UPDATE app_state SET
                        ads_enabled = ?, ads_removed_purchased = ?,
                        last_interstitial_time = ?, interstitial_count_today = ?,
                        last_count_reset_date = ?, max_pages_per_document = ?,
                        updated_at = ?
                    WHERE id = 1
                ''', (
                    1 if state.ads_enabled else 0,
                    1 if state.ads_removed_purchased else 0,
                    last_interstitial,
                    state.interstitial_count_today,
                    state.last_count_reset_date,
                    state.max_pages_per_document,
                    now
                ))
            else:
                self.db.execute('''
                    INSERT INTO app_state 
                    (id, ads_enabled, ads_removed_purchased, last_interstitial_time,
                     interstitial_count_today, last_count_reset_date, 
                     max_pages_per_document, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    1 if state.ads_enabled else 0,
                    1 if state.ads_removed_purchased else 0,
                    last_interstitial,
                    state.interstitial_count_today,
                    state.last_count_reset_date,
                    state.max_pages_per_document,
                    now
                ))
            return True
        except Exception as e:
            Logger.error(f"AppStateRepository: Save failed: {e}")
            return False
    
    def _row_to_state(self, row) -> AppState:
        """Convert database row to AppState object."""
        last_time = None
        if row['last_interstitial_time']:
            try:
                last_time = datetime.fromisoformat(row['last_interstitial_time'])
            except:
                pass
        
        return AppState(
            ads_enabled=bool(row['ads_enabled']),
            ads_removed_purchased=bool(row['ads_removed_purchased']),
            last_interstitial_time=last_time,
            interstitial_count_today=row['interstitial_count_today'] or 0,
            last_count_reset_date=row['last_count_reset_date'],
            max_pages_per_document=row['max_pages_per_document'] or 200,
        )
