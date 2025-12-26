"""
PDF Viewer Bridge for PDF Scanner App.
Python wrapper to launch native PDF viewer from Kivy.
"""
from typing import Optional, Callable
from kivy.logger import Logger

from app.android_bridge.jnius_api import (
    is_android, 
    get_activity, 
    run_on_ui_thread,
    get_java_class
)


class PdfViewerBridge:
    """
    Bridge to launch native PDF viewer activity.
    
    Usage:
        viewer = PdfViewerBridge()
        viewer.open_pdf("/path/to/file.pdf", on_result=callback)
    """
    
    # Request code for activity result
    REQUEST_CODE = 9001
    
    # Result codes matching Java
    RESULT_SAVED = 1
    
    def __init__(self):
        self._on_result_callback: Optional[Callable] = None
        self._pending_path: Optional[str] = None
    
    def open_pdf(self, pdf_path: str, on_result: Optional[Callable] = None) -> bool:
        """
        Open a PDF file in the native viewer.
        
        Args:
            pdf_path: Absolute path to the PDF file
            on_result: Optional callback(saved_path: str or None)
        
        Returns:
            True if viewer was launched, False otherwise
        """
        if not is_android():
            Logger.warning("PdfViewer: Not on Android, viewer unavailable")
            return False
        
        if not pdf_path:
            Logger.error("PdfViewer: No PDF path provided")
            return False
        
        self._on_result_callback = on_result
        self._pending_path = pdf_path
        
        try:
            self._launch_viewer(pdf_path)
            return True
        except Exception as e:
            Logger.error(f"PdfViewer: Failed to launch: {e}")
            return False
    
    @run_on_ui_thread
    def _launch_viewer(self, pdf_path: str):
        """Launch the viewer on UI thread."""
        from jnius import autoclass
        
        activity = get_activity()
        if not activity:
            Logger.error("PdfViewer: No activity available")
            return
        
        Intent = autoclass('android.content.Intent')
        PdfViewerActivity = get_java_class('PdfViewerActivity')
        
        if PdfViewerActivity is None:
            Logger.error("PdfViewer: PdfViewerActivity class not found")
            return
        
        intent = Intent(activity, PdfViewerActivity)
        intent.putExtra("pdf_path", pdf_path)
        
        # Start activity for result if we have a callback
        if self._on_result_callback:
            activity.startActivityForResult(intent, self.REQUEST_CODE)
        else:
            activity.startActivity(intent)
        
        Logger.info(f"PdfViewer: Launched for {pdf_path}")
    
    def handle_activity_result(self, request_code: int, result_code: int, 
                                intent) -> bool:
        """
        Handle activity result from PDF viewer.
        Call this from your activity's on_activity_result.
        
        Returns:
            True if this was our result, False otherwise
        """
        if request_code != self.REQUEST_CODE:
            return False
        
        saved_path = None
        
        if result_code == self.RESULT_SAVED and intent:
            try:
                saved_path = intent.getStringExtra("saved_path")
                Logger.info(f"PdfViewer: Got saved path: {saved_path}")
            except Exception as e:
                Logger.error(f"PdfViewer: Error getting result: {e}")
        
        if self._on_result_callback:
            try:
                self._on_result_callback(saved_path)
            except Exception as e:
                Logger.error(f"PdfViewer: Callback error: {e}")
        
        self._on_result_callback = None
        self._pending_path = None
        
        return True


class PdfImporter:
    """
    Helper to import PDFs from file picker.
    """
    
    REQUEST_CODE = 9002
    
    def __init__(self):
        self._on_import_callback: Optional[Callable] = None
    
    def pick_pdf(self, on_import: Callable[[Optional[str]], None]) -> bool:
        """
        Open file picker for PDF selection.
        
        Args:
            on_import: Callback with imported file path (or None if cancelled)
        
        Returns:
            True if picker was launched
        """
        if not is_android():
            Logger.warning("PdfImporter: Not on Android")
            return False
        
        self._on_import_callback = on_import
        
        try:
            self._launch_picker()
            return True
        except Exception as e:
            Logger.error(f"PdfImporter: Failed to launch picker: {e}")
            return False
    
    @run_on_ui_thread
    def _launch_picker(self):
        """Launch file picker on UI thread."""
        from jnius import autoclass
        
        activity = get_activity()
        if not activity:
            return
        
        Intent = autoclass('android.content.Intent')
        
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/pdf")
        
        activity.startActivityForResult(intent, self.REQUEST_CODE)
        Logger.info("PdfImporter: Launched file picker")
    
    def handle_activity_result(self, request_code: int, result_code: int,
                                intent) -> bool:
        """
        Handle file picker result.
        
        Returns:
            True if this was our result
        """
        if request_code != self.REQUEST_CODE:
            return False
        
        imported_path = None
        
        # RESULT_OK = -1
        if result_code == -1 and intent:
            try:
                uri = intent.getData()
                if uri:
                    imported_path = self._copy_uri_to_storage(uri)
            except Exception as e:
                Logger.error(f"PdfImporter: Error handling result: {e}")
        
        if self._on_import_callback:
            try:
                self._on_import_callback(imported_path)
            except Exception as e:
                Logger.error(f"PdfImporter: Callback error: {e}")
        
        self._on_import_callback = None
        
        return True
    
    def _copy_uri_to_storage(self, uri) -> Optional[str]:
        """Copy content URI to app storage."""
        try:
            from jnius import autoclass
            
            activity = get_activity()
            if not activity:
                return None
            
            UriFileCopier = get_java_class('UriFileCopier')
            if UriFileCopier is None:
                Logger.error("PdfImporter: UriFileCopier not found")
                return None
            
            File = autoclass('java.io.File')
            files_dir = activity.getFilesDir()
            import_dir = File(files_dir, "imported")
            
            result = UriFileCopier.copyToPrivateStorage(
                activity, uri, import_dir, None)
            
            return result
            
        except Exception as e:
            Logger.error(f"PdfImporter: Copy failed: {e}")
            return None


# Global instances
_viewer_bridge: Optional[PdfViewerBridge] = None
_importer: Optional[PdfImporter] = None


def get_pdf_viewer() -> PdfViewerBridge:
    """Get the global PDF viewer bridge instance."""
    global _viewer_bridge
    if _viewer_bridge is None:
        _viewer_bridge = PdfViewerBridge()
    return _viewer_bridge


def get_pdf_importer() -> PdfImporter:
    """Get the global PDF importer instance."""
    global _importer
    if _importer is None:
        _importer = PdfImporter()
    return _importer


def open_pdf(pdf_path: str, on_result: Optional[Callable] = None) -> bool:
    """Convenience function to open PDF viewer."""
    return get_pdf_viewer().open_pdf(pdf_path, on_result)


def import_pdf(on_import: Callable[[Optional[str]], None]) -> bool:
    """Convenience function to import PDF."""
    return get_pdf_importer().pick_pdf(on_import)
