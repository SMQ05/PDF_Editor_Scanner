"""
Home Screen for PDF Scanner App.
Main entry point with scan button, import, and recent documents.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App

from app.ui.theme import get_theme
from app.ui.widgets import RoundedButton, DocumentCard


class HomeScreen(Screen):
    """Home screen with scan button and recent documents."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = get_theme()
        self.recent_documents = []
        self._build_ui()
    
    def _build_ui(self):
        """Build the home screen UI."""
        # Main container
        main_layout = BoxLayout(orientation='vertical', padding=16, spacing=16)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=60, spacing=8)
        
        title = Label(
            text='PDF Scanner',
            font_size='28sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            valign='middle',
            bold=True
        )
        title.bind(size=lambda *x: setattr(title, 'text_size', (title.width, None)))
        header.add_widget(title)
        
        # Settings button
        settings_btn = RoundedButton(
            text='⚙',
            variant='outline',
            size_hint=(None, None),
            size=(48, 48)
        )
        settings_btn.bind(on_release=self._on_settings)
        header.add_widget(settings_btn)
        
        main_layout.add_widget(header)
        
        # Action buttons
        buttons_layout = BoxLayout(size_hint_y=None, height=56, spacing=12)
        
        scan_btn = RoundedButton(
            text='📷  Scan Document',
            variant='primary',
            font_size='18sp'
        )
        scan_btn.bind(on_release=self._on_scan)
        buttons_layout.add_widget(scan_btn)
        
        import_btn = RoundedButton(
            text='📁  Import',
            variant='secondary',
            size_hint_x=0.4
        )
        import_btn.bind(on_release=self._on_import)
        buttons_layout.add_widget(import_btn)
        
        main_layout.add_widget(buttons_layout)
        
        # Recent documents section
        recent_header = Label(
            text='Recent Documents',
            font_size='18sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=40
        )
        recent_header.bind(size=lambda *x: setattr(recent_header, 'text_size', (recent_header.width, None)))
        main_layout.add_widget(recent_header)
        
        # Recent documents list
        self.recents_container = BoxLayout(
            orientation='vertical',
            spacing=8,
            size_hint_y=None
        )
        self.recents_container.bind(minimum_height=self.recents_container.setter('height'))
        
        recents_scroll = ScrollView(size_hint=(1, 1))
        recents_scroll.add_widget(self.recents_container)
        main_layout.add_widget(recents_scroll)
        
        # Banner ad placeholder (at bottom)
        self.banner_container = BoxLayout(size_hint_y=None, height=60)
        self._update_banner_placeholder()
        main_layout.add_widget(self.banner_container)
        
        # Set background
        with main_layout.canvas.before:
            Color(*self.theme.get_color('background'))
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(pos=self._update_bg, size=self._update_bg)
        
        self.add_widget(main_layout)
        self.main_layout = main_layout
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.main_layout.pos
        self.bg_rect.size = self.main_layout.size
    
    def _update_banner_placeholder(self):
        """Update the banner ad area."""
        self.banner_container.clear_widgets()
        
        # Show banner placeholder or actual ad
        app = App.get_running_app()
        if app and hasattr(app, 'ads_manager') and app.ads_manager:
            if app.ads_manager.should_show_ads():
                # Show banner
                banner_label = Label(
                    text='[Ad Banner Area]',
                    font_size='12sp',
                    color=[0.5, 0.5, 0.5, 0.5]
                )
                self.banner_container.add_widget(banner_label)
                # Trigger native banner
                app.ads_manager.show_banner()
            else:
                # No ads - hide container
                self.banner_container.height = 0
    
    def on_enter(self):
        """Called when screen is shown."""
        self._load_recent_documents()
        self._update_banner_placeholder()
    
    def _load_recent_documents(self):
        """Load and display recent documents."""
        self.recents_container.clear_widgets()
        
        try:
            app = App.get_running_app()
            if app and app.db_manager:
                from app.infra.storage.repositories import DocumentRepository
                doc_repo = DocumentRepository(app.db_manager)
                self.recent_documents = doc_repo.get_all_documents(limit=20)
                
                if not self.recent_documents:
                    # Show empty state
                    empty_label = Label(
                        text='No documents yet.\nTap "Scan Document" to get started!',
                        font_size='14sp',
                        color=self.theme.get_color('on_surface_variant'),
                        halign='center',
                        valign='middle',
                        size_hint_y=None,
                        height=100
                    )
                    empty_label.bind(size=lambda *x: setattr(empty_label, 'text_size', (empty_label.width, None)))
                    self.recents_container.add_widget(empty_label)
                else:
                    # Add document cards
                    for doc in self.recent_documents:
                        card = DocumentCard(
                            document=doc,
                            on_tap=self._on_document_tap,
                            on_long_press=self._on_document_long_press
                        )
                        self.recents_container.add_widget(card)
        except Exception as e:
            Logger.error(f"Home: Failed to load documents: {e}")
    
    def _on_scan(self, *args):
        """Navigate to scanner screen."""
        self.manager.current = 'scanner'
    
    def _on_import(self, *args):
        """Open file picker to import PDF or images."""
        try:
            from app.android_bridge import import_pdf, is_android
            
            if is_android():
                # Use native PDF importer on Android
                import_pdf(self._on_pdf_imported)
            else:
                # Fallback to plyer file chooser
                from plyer import filechooser
                filechooser.open_file(
                    on_selection=self._on_files_selected,
                    filters=['*.jpg', '*.jpeg', '*.png', '*.pdf'],
                    multiple=True
                )
        except Exception as e:
            Logger.error(f"Home: File picker failed: {e}")
    
    def _on_pdf_imported(self, pdf_path):
        """Handle imported PDF file - open in viewer."""
        if pdf_path:
            Logger.info(f"Home: Imported PDF: {pdf_path}")
            self._open_pdf_viewer(pdf_path)
        else:
            Logger.info("Home: PDF import cancelled")
    
    def _on_files_selected(self, selection):
        """Handle imported files (desktop fallback)."""
        if selection:
            Logger.info(f"Home: Selected files: {selection}")
            # If PDF, open in viewer (if available)
            for path in selection:
                if path.lower().endswith('.pdf'):
                    self._open_pdf_viewer(path)
                    return
            # TODO: Process image files
    
    def _on_settings(self, *args):
        """Navigate to settings screen."""
        self.manager.current = 'settings'
    
    def _on_document_tap(self, document):
        """Handle document tap - open in PDF viewer."""
        Logger.info(f"Home: Tapped document {document.name}")
        if document.file_path:
            self._open_pdf_viewer(document.file_path)
    
    def _open_pdf_viewer(self, pdf_path):
        """Open PDF in native viewer."""
        try:
            from app.android_bridge import open_pdf, is_android
            
            if is_android():
                def on_viewer_result(saved_path):
                    if saved_path:
                        Logger.info(f"Home: PDF saved to {saved_path}")
                        # Refresh recents
                        Clock.schedule_once(lambda dt: self._load_recent_documents(), 0.5)
                
                open_pdf(pdf_path, on_viewer_result)
            else:
                # Desktop fallback - just share
                from app.android_bridge.intents import share_file
                share_file(pdf_path, 'application/pdf', 'Open PDF')
        except Exception as e:
            Logger.error(f"Home: Failed to open PDF: {e}")
    
    def _on_document_long_press(self, document):
        """Handle document long press - show share option."""
        Logger.info(f"Home: Long press on {document.name}")
        if document.file_path:
            from app.android_bridge.intents import share_file
            share_file(document.file_path, 'application/pdf', 'Share PDF')
