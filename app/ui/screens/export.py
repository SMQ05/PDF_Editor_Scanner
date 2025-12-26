"""
Export Screen for PDF Scanner App.
PDF export with compression presets and sharing.
"""
import os
from typing import Optional
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App

from app.ui.theme import get_theme
from app.ui.widgets import RoundedButton
from app.domain.models import ScanSession, CompressionPreset


class ExportScreen(Screen):
    """Screen for exporting scan session to PDF."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = get_theme()
        self.session: Optional[ScanSession] = None
        self.selected_preset: CompressionPreset = CompressionPreset.BALANCED
        self.output_path: Optional[str] = None
        self.is_exporting = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the export screen UI."""
        root = BoxLayout(orientation='vertical', padding=16, spacing=16)
        
        # Background
        with root.canvas.before:
            Color(*self.theme.get_color('background'))
            self.bg_rect = Rectangle()
        root.bind(pos=self._update_bg, size=self._update_bg)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=56, spacing=8)
        
        back_btn = RoundedButton(
            text='←',
            variant='outline',
            size_hint=(None, None),
            size=(48, 48)
        )
        back_btn.bind(on_release=self._on_back)
        header.add_widget(back_btn)
        
        title = Label(
            text='Export PDF',
            font_size='22sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            valign='middle',
            bold=True
        )
        title.bind(size=lambda *x: setattr(title, 'text_size', (title.width, None)))
        header.add_widget(title)
        
        root.add_widget(header)
        
        # Pages preview
        preview_label = Label(
            text='Pages',
            font_size='16sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            size_hint_y=None,
            height=30
        )
        preview_label.bind(size=lambda *x: setattr(preview_label, 'text_size', (preview_label.width, None)))
        root.add_widget(preview_label)
        
        # Horizontal scroll of page thumbnails
        self.pages_scroll = ScrollView(
            do_scroll_y=False,
            size_hint_y=None,
            height=120
        )
        
        self.pages_container = BoxLayout(
            orientation='horizontal',
            spacing=8,
            size_hint_x=None,
            padding=4
        )
        self.pages_container.bind(minimum_width=self.pages_container.setter('width'))
        
        self.pages_scroll.add_widget(self.pages_container)
        root.add_widget(self.pages_scroll)
        
        # Filename input
        filename_label = Label(
            text='Filename',
            font_size='16sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            size_hint_y=None,
            height=30
        )
        filename_label.bind(size=lambda *x: setattr(filename_label, 'text_size', (filename_label.width, None)))
        root.add_widget(filename_label)
        
        self.filename_input = TextInput(
            text='Scanned_Document',
            multiline=False,
            size_hint_y=None,
            height=48,
            font_size='16sp',
            background_color=[0.95, 0.95, 0.95, 1],
            foreground_color=[0.1, 0.1, 0.1, 1],
            padding=[12, 12]
        )
        root.add_widget(self.filename_input)
        
        # Compression presets
        preset_label = Label(
            text='Quality Preset',
            font_size='16sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            size_hint_y=None,
            height=30
        )
        preset_label.bind(size=lambda *x: setattr(preset_label, 'text_size', (preset_label.width, None)))
        root.add_widget(preset_label)
        
        presets_layout = BoxLayout(size_hint_y=None, height=80, spacing=12)
        
        self.preset_buttons = {}
        for preset in CompressionPreset:
            desc = {
                CompressionPreset.SMALL: "Small\n~0.5MB/page",
                CompressionPreset.BALANCED: "Balanced\n~1MB/page",
                CompressionPreset.HIGH: "High\n~2MB/page",
            }
            
            btn = RoundedButton(
                text=desc.get(preset, preset.value),
                variant='secondary' if preset != self.selected_preset else 'primary',
                font_size='13sp'
            )
            btn.preset = preset
            btn.bind(on_release=self._on_preset_select)
            self.preset_buttons[preset] = btn
            presets_layout.add_widget(btn)
        
        root.add_widget(presets_layout)
        
        # Size estimate
        self.size_estimate = Label(
            text='Estimated size: calculating...',
            font_size='14sp',
            color=self.theme.get_color('on_surface_variant'),
            halign='left',
            size_hint_y=None,
            height=24
        )
        self.size_estimate.bind(size=lambda *x: setattr(self.size_estimate, 'text_size', (self.size_estimate.width, None)))
        root.add_widget(self.size_estimate)
        
        root.add_widget(Widget())  # Spacer
        
        # Progress bar (hidden by default)
        self.progress_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=60,
            spacing=8
        )
        self.progress_container.opacity = 0
        
        self.progress_label = Label(
            text='Exporting...',
            font_size='14sp',
            color=self.theme.get_color('on_surface'),
            size_hint_y=None,
            height=20
        )
        self.progress_container.add_widget(self.progress_label)
        
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )
        self.progress_container.add_widget(self.progress_bar)
        
        root.add_widget(self.progress_container)
        
        # Action buttons
        actions = BoxLayout(size_hint_y=None, height=56, spacing=16)
        
        self.export_btn = RoundedButton(
            text='Export PDF',
            variant='primary'
        )
        self.export_btn.bind(on_release=self._on_export)
        actions.add_widget(self.export_btn)
        
        self.share_btn = RoundedButton(
            text='Share',
            variant='secondary'
        )
        self.share_btn.bind(on_release=self._on_share)
        self.share_btn.disabled = True
        actions.add_widget(self.share_btn)
        
        root.add_widget(actions)
        
        self.add_widget(root)
        self.root_layout = root
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.root_layout.pos
        self.bg_rect.size = self.root_layout.size
    
    def set_session(self, session: ScanSession):
        """Set the session to export."""
        self.session = session
        self.output_path = None
        self.share_btn.disabled = True
        self._update_pages_preview()
        self._update_filename()
        self._update_size_estimate()
    
    def _update_pages_preview(self):
        """Update the pages thumbnail preview."""
        self.pages_container.clear_widgets()
        
        if not self.session or not self.session.pages:
            return
        
        for i, page in enumerate(self.session.pages):
            # Create thumbnail container
            thumb_container = BoxLayout(
                orientation='vertical',
                size_hint=(None, None),
                size=(80, 110),
                spacing=4
            )
            
            # Thumbnail image
            if page.image_path and os.path.exists(page.image_path):
                thumb = Image(
                    source=page.image_path,
                    allow_stretch=True,
                    keep_ratio=True,
                    size_hint=(None, None),
                    size=(80, 90)
                )
            else:
                thumb = Widget(size_hint=(None, None), size=(80, 90))
            
            thumb_container.add_widget(thumb)
            
            # Page number
            num_label = Label(
                text=str(i + 1),
                font_size='12sp',
                color=self.theme.get_color('on_surface'),
                size_hint_y=None,
                height=16
            )
            thumb_container.add_widget(num_label)
            
            self.pages_container.add_widget(thumb_container)
    
    def _update_filename(self):
        """Update default filename based on date."""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        self.filename_input.text = f"Scan_{timestamp}"
    
    def _update_size_estimate(self):
        """Update estimated file size."""
        if not self.session or not self.session.pages:
            self.size_estimate.text = "Estimated size: --"
            return
        
        # Get image paths
        image_paths = [p.image_path for p in self.session.pages if p.image_path]
        
        from app.infra.pdf.pdf_compress import estimate_output_size, format_file_size
        estimated = estimate_output_size(image_paths, self.selected_preset.value)
        self.size_estimate.text = f"Estimated size: {format_file_size(estimated)}"
    
    def _on_preset_select(self, btn):
        """Handle preset selection."""
        self.selected_preset = btn.preset
        
        # Update button styles
        for preset, button in self.preset_buttons.items():
            if preset == self.selected_preset:
                button.bg_color = self.theme.get_color('primary')
                button.color = self.theme.get_color('on_primary')
            else:
                button.bg_color = self.theme.get_color('secondary_container')
                button.color = self.theme.get_color('on_surface')
            button._update_canvas()
        
        self._update_size_estimate()
    
    def _on_export(self, *args):
        """Export to PDF."""
        if self.is_exporting or not self.session or not self.session.pages:
            return
        
        self.is_exporting = True
        self.export_btn.disabled = True
        self.progress_container.opacity = 1
        self.progress_bar.value = 0
        
        app = App.get_running_app()
        if not app:
            return
        
        filename = self.filename_input.text.strip() or "Scanned_Document"
        
        # Export using use case
        from app.domain.usecases import ExportPDFUseCase
        from app.infra.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(app.db_manager)
        export_uc = ExportPDFUseCase(doc_repo, app.get_documents_path())
        
        def progress_update(current, total):
            progress = (current / total) * 100
            self.progress_bar.value = progress
            self.progress_label.text = f"Processing page {current}/{total}..."
        
        def do_export():
            result = export_uc.export_session_to_pdf(
                session=self.session,
                filename=filename,
                preset=self.selected_preset,
                progress_callback=progress_update
            )
            
            def on_complete(dt):
                self.is_exporting = False
                self.export_btn.disabled = False
                
                if result.success:
                    self.output_path = result.output_path
                    self.share_btn.disabled = False
                    self.progress_label.text = "Export complete!"
                    
                    # Show interstitial if allowed
                    if app.ads_manager and app.ads_manager.can_show_interstitial():
                        app.ads_manager.show_interstitial()
                    
                    # Clear the scan session
                    scanner_screen = self.manager.get_screen('scanner')
                    scanner_screen.clear_session()
                    
                    Logger.info(f"Export: PDF created at {result.output_path}")
                else:
                    self.progress_label.text = f"Export failed: {result.error_message}"
                    Logger.error(f"Export: Failed - {result.error_message}")
                
                # Hide progress after delay
                Clock.schedule_once(lambda dt: setattr(self.progress_container, 'opacity', 0), 3)
            
            Clock.schedule_once(on_complete, 0)
        
        # Run export in background
        import threading
        threading.Thread(target=do_export, daemon=True).start()
    
    def _on_share(self, *args):
        """Share the exported PDF."""
        if not self.output_path or not os.path.exists(self.output_path):
            return
        
        from app.android_bridge.intents import share_file
        share_file(self.output_path, 'application/pdf', 'Share PDF')
        
        # Show interstitial after share
        app = App.get_running_app()
        if app and app.ads_manager and app.ads_manager.can_show_interstitial():
            Clock.schedule_once(lambda dt: app.ads_manager.show_interstitial(), 0.5)
    
    def _on_back(self, *args):
        """Go back to scanner."""
        self.manager.current = 'scanner'
