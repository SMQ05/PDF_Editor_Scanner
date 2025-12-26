"""
Domain Use Cases for PDF Scanner App.
Business logic orchestration.
"""
import os
import threading
from typing import List, Optional, Callable
from datetime import datetime
from kivy.logger import Logger
from kivy.utils import platform
from kivy.clock import Clock

from .models import (
    Page, Document, ScanSession, AppState, 
    FilterType, CompressionPreset, ProcessingResult
)


class AdsManager:
    """Manages ad display logic and purchase state."""
    
    def __init__(self, app_state_repo):
        self.app_state_repo = app_state_repo
        self.app_state: AppState = AppState()
        self._initialized = False
        self._admob = None
        self._billing = None
        
    def initialize(self):
        """Initialize ads SDK and restore purchase state."""
        if self._initialized:
            return
            
        try:
            # Load saved state from DB
            saved_state = self.app_state_repo.get_app_state()
            if saved_state:
                self.app_state = saved_state
            
            if platform == 'android':
                from app.android_bridge.admob import AdMobBridge
                from app.android_bridge.billing import BillingBridge
                
                self._admob = AdMobBridge()
                self._billing = BillingBridge()
                
                # Restore purchases
                self._billing.restore_purchases(self._on_purchase_restored)
                
            self._initialized = True
            Logger.info("AdsManager: Initialized successfully")
        except Exception as e:
            Logger.error(f"AdsManager: Initialization failed: {e}")
    
    def _on_purchase_restored(self, is_purchased: bool):
        """Callback when purchase state is restored."""
        self.app_state.ads_removed_purchased = is_purchased
        if is_purchased:
            self.app_state.ads_enabled = False
        self._save_state()
        Logger.info(f"AdsManager: Purchase restored, ads_removed={is_purchased}")
    
    def refresh_purchase_state(self):
        """Refresh purchase state (for refund handling)."""
        if platform == 'android' and self._billing:
            self._billing.query_purchases(self._on_purchase_query)
    
    def _on_purchase_query(self, is_purchased: bool):
        """Callback for purchase query."""
        if self.app_state.ads_removed_purchased != is_purchased:
            self.app_state.ads_removed_purchased = is_purchased
            self.app_state.ads_enabled = not is_purchased
            self._save_state()
            Logger.info(f"AdsManager: Purchase state changed to {is_purchased}")
    
    def should_show_ads(self) -> bool:
        """Check if ads should be shown."""
        return self.app_state.ads_enabled and not self.app_state.ads_removed_purchased
    
    def show_banner(self):
        """Show banner ad if allowed."""
        if not self.should_show_ads():
            return
        if platform == 'android' and self._admob:
            self._admob.show_banner()
    
    def hide_banner(self):
        """Hide banner ad."""
        if platform == 'android' and self._admob:
            self._admob.hide_banner()
    
    def can_show_interstitial(self) -> bool:
        """Check if interstitial can be shown (frequency cap)."""
        return self.app_state.can_show_interstitial()
    
    def show_interstitial(self, callback: Optional[Callable] = None):
        """Show interstitial ad if allowed by frequency cap."""
        if not self.can_show_interstitial():
            if callback:
                callback(False)
            return
        
        if platform == 'android' and self._admob:
            def on_closed():
                self.app_state.record_interstitial_shown()
                self._save_state()
                if callback:
                    callback(True)
            
            self._admob.show_interstitial(on_closed)
        else:
            if callback:
                callback(False)
    
    def purchase_remove_ads(self, callback: Callable[[bool, str], None]):
        """Initiate remove ads purchase."""
        if platform == 'android' and self._billing:
            def on_purchase_result(success: bool, message: str):
                if success:
                    self.app_state.ads_removed_purchased = True
                    self.app_state.ads_enabled = False
                    self._save_state()
                    self.hide_banner()
                callback(success, message)
            
            self._billing.purchase_remove_ads(on_purchase_result)
        else:
            callback(False, "Billing not available")
    
    def restore_purchases(self, callback: Callable[[bool, str], None]):
        """Restore previous purchases."""
        if platform == 'android' and self._billing:
            def on_restore_result(is_purchased: bool):
                if is_purchased:
                    self.app_state.ads_removed_purchased = True
                    self.app_state.ads_enabled = False
                    self._save_state()
                    self.hide_banner()
                    callback(True, "Purchases restored successfully")
                else:
                    callback(False, "No previous purchases found")
            
            self._billing.restore_purchases(on_restore_result)
        else:
            callback(False, "Billing not available")
    
    def _save_state(self):
        """Save app state to database."""
        try:
            self.app_state_repo.save_app_state(self.app_state)
        except Exception as e:
            Logger.error(f"AdsManager: Failed to save state: {e}")


class ScanDocumentUseCase:
    """Orchestrates the document scanning workflow."""
    
    MAX_PAGES_DEFAULT = 200
    
    def __init__(self, session_store, document_repo, page_repo, storage_path: str):
        self.session_store = session_store
        self.document_repo = document_repo
        self.page_repo = page_repo
        self.storage_path = storage_path
        self.current_session: Optional[ScanSession] = None
        self._processing_lock = threading.Lock()
        
    def start_new_session(self) -> ScanSession:
        """Start a new scanning session."""
        self.current_session = ScanSession()
        self.session_store.save_session(self.current_session)
        Logger.info("ScanUseCase: Started new session")
        return self.current_session
    
    def get_or_create_session(self) -> ScanSession:
        """Get existing session or create new one."""
        if self.current_session is None:
            # Try to restore from storage
            self.current_session = self.session_store.get_active_session()
            if self.current_session is None:
                self.current_session = self.start_new_session()
        return self.current_session
    
    def can_add_page(self, max_pages: int = None) -> tuple:
        """Check if more pages can be added. Returns (can_add, warning_message)."""
        max_pages = max_pages or self.MAX_PAGES_DEFAULT
        session = self.get_or_create_session()
        current_count = len(session.pages)
        
        if current_count >= max_pages:
            return False, f"Maximum of {max_pages} pages reached"
        elif current_count >= max_pages - 10:
            return True, f"Warning: {max_pages - current_count} pages remaining"
        return True, ""
    
    def add_page(self, image_path: str, quad_points: List[tuple] = None, 
                 filter_type: FilterType = FilterType.ORIGINAL) -> Page:
        """Add a scanned page to the current session."""
        session = self.get_or_create_session()
        
        page = Page(
            image_path=image_path,
            quad_points=quad_points,
            filter_applied=filter_type,
            order=len(session.pages),
        )
        session.add_page(page)
        self.session_store.save_session(session)
        
        Logger.info(f"ScanUseCase: Added page {page.order + 1}")
        return page
    
    def update_page(self, page_index: int, **kwargs):
        """Update a page in the current session."""
        session = self.get_or_create_session()
        if 0 <= page_index < len(session.pages):
            page = session.pages[page_index]
            for key, value in kwargs.items():
                if hasattr(page, key):
                    setattr(page, key, value)
            self.session_store.save_session(session)
            Logger.info(f"ScanUseCase: Updated page {page_index}")
    
    def remove_page(self, page_index: int):
        """Remove a page from the current session."""
        session = self.get_or_create_session()
        if 0 <= page_index < len(session.pages):
            # Delete the image file
            page = session.pages[page_index]
            if page.image_path and os.path.exists(page.image_path):
                try:
                    os.remove(page.image_path)
                except Exception as e:
                    Logger.warning(f"ScanUseCase: Could not delete page image: {e}")
            
            session.remove_page(page_index)
            self.session_store.save_session(session)
            Logger.info(f"ScanUseCase: Removed page {page_index}")
    
    def complete_session(self) -> Optional[Document]:
        """Complete the session and return document info (PDF not yet created)."""
        session = self.get_or_create_session()
        if not session.pages:
            return None
        
        session.is_complete = True
        self.session_store.save_session(session)
        
        # Create document record (PDF will be created by export use case)
        doc = Document(
            name=f"Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            page_count=len(session.pages),
        )
        
        Logger.info(f"ScanUseCase: Session completed with {len(session.pages)} pages")
        return doc
    
    def clear_session(self):
        """Clear the current session and delete temporary files."""
        if self.current_session:
            for page in self.current_session.pages:
                if page.image_path and os.path.exists(page.image_path):
                    try:
                        os.remove(page.image_path)
                    except:
                        pass
            self.session_store.delete_session(self.current_session.id)
            self.current_session = None
            Logger.info("ScanUseCase: Session cleared")


class ExportPDFUseCase:
    """Handles PDF export with compression."""
    
    def __init__(self, document_repo, documents_path: str):
        self.document_repo = document_repo
        self.documents_path = documents_path
        
    def export_session_to_pdf(self, session: ScanSession, filename: str,
                              preset: CompressionPreset = CompressionPreset.BALANCED,
                              progress_callback: Callable[[int, int], None] = None) -> ProcessingResult:
        """Export scan session to PDF with specified compression."""
        from app.infra.pdf.pdf_build import PDFBuilder
        from app.infra.pdf.pdf_compress import compress_images_for_pdf
        from app.infra.imaging.exif_sanitize import sanitize_image
        
        result = ProcessingResult()
        start_time = datetime.now()
        
        try:
            if not session.pages:
                result.error_message = "No pages to export"
                return result
            
            # Ensure output directory exists
            os.makedirs(self.documents_path, exist_ok=True)
            
            # Prepare output path
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            output_path = os.path.join(self.documents_path, filename)
            
            # Process images with compression and sanitization
            processed_images = []
            total = len(session.pages)
            
            for i, page in enumerate(session.pages):
                if progress_callback:
                    Clock.schedule_once(lambda dt, idx=i: progress_callback(idx + 1, total), 0)
                
                if not os.path.exists(page.image_path):
                    Logger.warning(f"ExportUseCase: Page image not found: {page.image_path}")
                    continue
                
                # Sanitize (strip EXIF) and compress
                sanitized_path = sanitize_image(page.image_path)
                compressed_path = compress_images_for_pdf(
                    sanitized_path, 
                    preset.max_dimension, 
                    preset.jpeg_quality
                )
                processed_images.append(compressed_path)
            
            if not processed_images:
                result.error_message = "No valid images to export"
                return result
            
            # Build PDF
            builder = PDFBuilder()
            success = builder.images_to_pdf(processed_images, output_path)
            
            if success:
                result.success = True
                result.output_path = output_path
                
                # Save document record
                doc = Document(
                    name=os.path.splitext(filename)[0],
                    file_path=output_path,
                    page_count=len(processed_images),
                    file_size=os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                )
                self.document_repo.save_document(doc)
                
                Logger.info(f"ExportUseCase: PDF created at {output_path}")
            else:
                result.error_message = "Failed to create PDF"
            
            # Cleanup temp compressed images
            for img_path in processed_images:
                if img_path != page.image_path and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass
                        
        except Exception as e:
            Logger.error(f"ExportUseCase: Export failed: {e}")
            result.error_message = str(e)
        
        result.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result


class MergePDFsUseCase:
    """Handles merging multiple PDFs."""
    
    def __init__(self, documents_path: str):
        self.documents_path = documents_path
    
    def merge(self, pdf_paths: List[str], output_filename: str,
              progress_callback: Callable[[int, int], None] = None) -> ProcessingResult:
        """Merge multiple PDFs into one."""
        from app.infra.pdf.pdf_tools import PDFTools
        
        result = ProcessingResult()
        start_time = datetime.now()
        
        try:
            if len(pdf_paths) < 2:
                result.error_message = "Need at least 2 PDFs to merge"
                return result
            
            # Check for encrypted PDFs
            tools = PDFTools()
            for pdf_path in pdf_paths:
                if tools.is_encrypted(pdf_path):
                    result.error_message = f"Cannot merge encrypted PDF: {os.path.basename(pdf_path)}"
                    return result
            
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            output_path = os.path.join(self.documents_path, output_filename)
            
            success = tools.merge_pdfs(pdf_paths, output_path, progress_callback)
            
            if success:
                result.success = True
                result.output_path = output_path
                Logger.info(f"MergeUseCase: Merged {len(pdf_paths)} PDFs")
            else:
                result.error_message = "Merge operation failed"
                
        except Exception as e:
            Logger.error(f"MergeUseCase: Merge failed: {e}")
            result.error_message = str(e)
        
        result.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result


class SplitPDFUseCase:
    """Handles splitting PDF into page ranges."""
    
    def __init__(self, documents_path: str):
        self.documents_path = documents_path
    
    def split(self, pdf_path: str, page_ranges: List[tuple], 
              output_prefix: str) -> ProcessingResult:
        """Split PDF by page ranges. Each range is (start, end) 1-indexed."""
        from app.infra.pdf.pdf_tools import PDFTools
        
        result = ProcessingResult()
        start_time = datetime.now()
        
        try:
            tools = PDFTools()
            
            if tools.is_encrypted(pdf_path):
                result.error_message = "Cannot split encrypted PDF"
                return result
            
            output_paths = tools.split_pdf(pdf_path, page_ranges, 
                                           self.documents_path, output_prefix)
            
            if output_paths:
                result.success = True
                result.output_path = output_paths[0]  # First output
                Logger.info(f"SplitUseCase: Created {len(output_paths)} PDFs")
            else:
                result.error_message = "Split operation failed"
                
        except Exception as e:
            Logger.error(f"SplitUseCase: Split failed: {e}")
            result.error_message = str(e)
        
        result.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return result
