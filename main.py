"""
PDF Scanner - Android Document Scanner App
Main entry point for the Kivy application.
"""
import os
import sys

# Set environment variables before importing Kivy
os.environ['KIVY_LOG_LEVEL'] = 'info'
os.environ['KIVY_ORIENTATION'] = 'portrait'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform

# App modules
from app.ui.screens.home import HomeScreen
from app.ui.screens.scanner import ScannerScreen
from app.ui.screens.crop_adjust import CropAdjustScreen
from app.ui.screens.export import ExportScreen
from app.ui.screens.settings import SettingsScreen
from app.ui.theme import Theme
from app.infra.storage.db import DatabaseManager
from app.infra.storage.session_store import SessionStore
from app.infra.storage.repositories import AppStateRepository
from app.domain.usecases import AdsManager


class PDFScannerApp(App):
    """Main application class for PDF Scanner."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = Theme()
        self.db_manager = None
        self.session_store = None
        self.app_state_repo = None
        self.ads_manager = None
        self.screen_manager = None
        
    def build(self):
        """Build and return the root widget."""
        # Set window properties
        Window.clearcolor = self.theme.colors['background']
        
        # Initialize database
        self._init_database()
        
        # Initialize ads manager
        self._init_ads()
        
        # Create screen manager
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        # Add screens
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(ScannerScreen(name='scanner'))
        self.screen_manager.add_widget(CropAdjustScreen(name='crop_adjust'))
        self.screen_manager.add_widget(ExportScreen(name='export'))
        self.screen_manager.add_widget(SettingsScreen(name='settings'))
        
        # Restore session if needed
        Clock.schedule_once(self._restore_session, 0.5)
        
        return self.screen_manager
    
    def _init_database(self):
        """Initialize SQLite database and repositories."""
        try:
            db_path = self._get_db_path()
            self.db_manager = DatabaseManager(db_path)
            self.db_manager.initialize()
            self.session_store = SessionStore(self.db_manager)
            self.app_state_repo = AppStateRepository(self.db_manager)
            Logger.info("App: Database initialized successfully")
        except Exception as e:
            Logger.error(f"App: Failed to initialize database: {e}")
    
    def _init_ads(self):
        """Initialize ads manager and check purchase state."""
        try:
            self.ads_manager = AdsManager(self.app_state_repo)
            # Check if ads should be shown
            if platform == 'android':
                Clock.schedule_once(lambda dt: self.ads_manager.initialize(), 1.0)
            Logger.info("App: Ads manager initialized")
        except Exception as e:
            Logger.error(f"App: Failed to initialize ads: {e}")
    
    def _restore_session(self, dt):
        """Restore incomplete scan session if exists."""
        try:
            if self.session_store:
                session = self.session_store.get_active_session()
                if session and session.pages:
                    Logger.info(f"App: Restoring session with {len(session.pages)} pages")
                    scanner_screen = self.screen_manager.get_screen('scanner')
                    scanner_screen.restore_session(session)
        except Exception as e:
            Logger.error(f"App: Failed to restore session: {e}")
    
    def _get_db_path(self):
        """Get the database file path based on platform."""
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), 'pdf_scanner.db')
        else:
            # Desktop fallback for testing
            return os.path.join(os.path.dirname(__file__), 'pdf_scanner.db')
    
    def get_app_storage_path(self):
        """Get app-private storage path."""
        if platform == 'android':
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            return os.path.dirname(__file__)
    
    def get_cache_path(self):
        """Get cache directory path."""
        base = self.get_app_storage_path()
        cache_dir = os.path.join(base, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    def get_documents_path(self):
        """Get documents directory path."""
        base = self.get_app_storage_path()
        docs_dir = os.path.join(base, 'documents')
        os.makedirs(docs_dir, exist_ok=True)
        return docs_dir
    
    def on_pause(self):
        """Called when the app is paused (Android)."""
        Logger.info("App: Pausing - saving session")
        try:
            scanner_screen = self.screen_manager.get_screen('scanner')
            if hasattr(scanner_screen, 'save_session'):
                scanner_screen.save_session()
        except Exception as e:
            Logger.error(f"App: Error saving session on pause: {e}")
        return True
    
    def on_resume(self):
        """Called when the app resumes (Android)."""
        Logger.info("App: Resuming")
        # Refresh ads state in case of refund
        if self.ads_manager:
            self.ads_manager.refresh_purchase_state()
    
    def on_stop(self):
        """Called when the app is stopping."""
        Logger.info("App: Stopping")
        try:
            scanner_screen = self.screen_manager.get_screen('scanner')
            if hasattr(scanner_screen, 'save_session'):
                scanner_screen.save_session()
            if self.db_manager:
                self.db_manager.close()
        except Exception as e:
            Logger.error(f"App: Error on stop: {e}")


def main():
    """Main entry point."""
    PDFScannerApp().run()


if __name__ == '__main__':
    main()
