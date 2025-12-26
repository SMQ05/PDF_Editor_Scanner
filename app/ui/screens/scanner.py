"""
Scanner Screen for PDF Scanner App.
Camera preview with document edge detection overlay.
"""
import os
from typing import Optional, List, Tuple
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App
from kivy.utils import platform
from kivy.properties import BooleanProperty, ObjectProperty

from app.ui.theme import get_theme
from app.ui.widgets import RoundedButton, PageCounter
from app.domain.models import ScanSession, Page, FilterType, QuadResult


class ScannerScreen(Screen):
    """Scanner screen with live camera preview and document detection."""
    
    camera_ready = BooleanProperty(False)
    session = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = get_theme()
        self.session: Optional[ScanSession] = None
        self.pipeline = None
        self.current_quad: Optional[QuadResult] = None
        self.flash_on = False
        self.low_light_warning = False
        self._permission_requested = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the scanner screen UI."""
        # Root layout
        root = FloatLayout()
        
        # Camera placeholder (will be replaced with actual camera)
        self.camera_container = RelativeLayout()
        with self.camera_container.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.camera_bg = Rectangle(size=self.camera_container.size)
        self.camera_container.bind(size=self._update_camera_bg)
        root.add_widget(self.camera_container)
        
        # Overlay for quad drawing
        self.overlay = Widget()
        self.camera_container.add_widget(self.overlay)
        
        # Permission/error message
        self.message_label = Label(
            text='',
            font_size='16sp',
            color=[1, 1, 1, 0.9],
            halign='center',
            valign='middle',
            size_hint=(0.8, None),
            height=100,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.message_label.bind(size=lambda *x: setattr(self.message_label, 'text_size', (self.message_label.width, None)))
        root.add_widget(self.message_label)
        
        # Top bar
        top_bar = BoxLayout(
            size_hint=(1, None),
            height=60,
            padding=[16, 8],
            spacing=8,
            pos_hint={'top': 1}
        )
        
        # Back button
        back_btn = RoundedButton(
            text='←',
            variant='outline',
            size_hint=(None, None),
            size=(48, 48)
        )
        back_btn.bind(on_release=self._on_back)
        top_bar.add_widget(back_btn)
        
        top_bar.add_widget(Widget())  # Spacer
        
        # Page counter
        self.page_counter = PageCounter(
            size_hint=(None, None),
            size=(80, 48)
        )
        top_bar.add_widget(self.page_counter)
        
        # Flash toggle
        self.flash_btn = RoundedButton(
            text='⚡',
            variant='outline',
            size_hint=(None, None),
            size=(48, 48)
        )
        self.flash_btn.bind(on_release=self._on_flash_toggle)
        top_bar.add_widget(self.flash_btn)
        
        root.add_widget(top_bar)
        
        # Low light warning
        self.low_light_label = Label(
            text='⚠ Low light - consider using flash',
            font_size='12sp',
            color=[1, 0.8, 0, 1],
            size_hint=(1, None),
            height=30,
            pos_hint={'top': 0.9}
        )
        self.low_light_label.opacity = 0
        root.add_widget(self.low_light_label)
        
        # Bottom controls
        bottom_bar = BoxLayout(
            size_hint=(1, None),
            height=120,
            padding=[20, 16],
            spacing=20,
            pos_hint={'y': 0}
        )
        
        # Gallery/preview of captured pages
        self.preview_btn = RoundedButton(
            text='📄',
            variant='secondary',
            size_hint=(None, None),
            size=(56, 56)
        )
        self.preview_btn.bind(on_release=self._on_preview)
        bottom_bar.add_widget(self.preview_btn)
        
        bottom_bar.add_widget(Widget())  # Spacer
        
        # Capture button (large, centered)
        capture_btn = BoxLayout(size_hint=(None, None), size=(80, 80))
        self.capture_btn_inner = RoundedButton(
            text='',
            variant='primary',
            size_hint=(1, 1),
            radius=40
        )
        self.capture_btn_inner.bind(on_release=self._on_capture)
        capture_btn.add_widget(self.capture_btn_inner)
        bottom_bar.add_widget(capture_btn)
        
        bottom_bar.add_widget(Widget())  # Spacer
        
        # Done button
        self.done_btn = RoundedButton(
            text='Done',
            variant='primary',
            size_hint=(None, None),
            size=(80, 56)
        )
        self.done_btn.bind(on_release=self._on_done)
        self.done_btn.disabled = True
        bottom_bar.add_widget(self.done_btn)
        
        root.add_widget(bottom_bar)
        
        self.add_widget(root)
        self.root_layout = root
    
    def _update_camera_bg(self, *args):
        self.camera_bg.size = self.camera_container.size
    
    def on_enter(self):
        """Called when screen is shown."""
        self._check_permission_and_start()
    
    def on_leave(self):
        """Called when leaving screen."""
        self._stop_camera()
        self.save_session()
    
    def _check_permission_and_start(self):
        """Check camera permission and start preview."""
        if platform == 'android':
            from app.android_bridge.intents import check_camera_permission, request_camera_permission, is_permission_denied_permanently
            
            if check_camera_permission():
                self._start_camera()
            elif is_permission_denied_permanently():
                self._show_permission_denied_permanently()
            else:
                self._show_permission_rationale()
        else:
            # Desktop - start directly
            self._start_camera()
    
    def _show_permission_rationale(self):
        """Show camera permission rationale."""
        self.message_label.text = (
            "Camera access is needed to scan documents.\n\n"
            "Tap 'Grant Permission' to continue."
        )
        
        # Add grant button if not already added
        if not hasattr(self, 'grant_btn') or self.grant_btn.parent is None:
            self.grant_btn = RoundedButton(
                text='Grant Permission',
                variant='primary',
                size_hint=(None, None),
                size=(200, 48),
                pos_hint={'center_x': 0.5, 'center_y': 0.35}
            )
            self.grant_btn.bind(on_release=self._request_permission)
            self.root_layout.add_widget(self.grant_btn)
    
    def _show_permission_denied_permanently(self):
        """Show message for permanently denied permission."""
        self.message_label.text = (
            "Camera permission was denied.\n\n"
            "Please enable it in Settings to scan documents."
        )
        
        # Add settings button
        if not hasattr(self, 'settings_btn') or self.settings_btn.parent is None:
            self.settings_btn = RoundedButton(
                text='Open Settings',
                variant='primary',
                size_hint=(None, None),
                size=(200, 48),
                pos_hint={'center_x': 0.5, 'center_y': 0.35}
            )
            self.settings_btn.bind(on_release=self._open_settings)
            self.root_layout.add_widget(self.settings_btn)
    
    def _request_permission(self, *args):
        """Request camera permission."""
        from app.android_bridge.intents import request_camera_permission
        
        def on_result(granted):
            if granted:
                self._hide_permission_ui()
                self._start_camera()
            else:
                from app.android_bridge.intents import is_permission_denied_permanently
                if is_permission_denied_permanently():
                    self._show_permission_denied_permanently()
        
        request_camera_permission(on_result)
    
    def _open_settings(self, *args):
        """Open app settings for permission."""
        from app.android_bridge.intents import open_app_settings
        open_app_settings()
    
    def _hide_permission_ui(self):
        """Hide permission request UI."""
        self.message_label.text = ''
        if hasattr(self, 'grant_btn') and self.grant_btn.parent:
            self.root_layout.remove_widget(self.grant_btn)
        if hasattr(self, 'settings_btn') and self.settings_btn.parent:
            self.root_layout.remove_widget(self.settings_btn)
    
    def _start_camera(self):
        """Start camera preview."""
        self._hide_permission_ui()
        
        try:
            # Initialize pipeline
            app = App.get_running_app()
            if app:
                from app.infra.imaging.scanner_pipeline import ScannerPipeline
                self.pipeline = ScannerPipeline(app.get_cache_path())
            
            # Start camera (platform-specific)
            if platform == 'android':
                self._start_android_camera()
            else:
                self._start_desktop_camera()
            
            self.camera_ready = True
            Logger.info("Scanner: Camera started")
            
        except Exception as e:
            Logger.error(f"Scanner: Failed to start camera: {e}")
            self.message_label.text = f"Camera error: {e}"
    
    def _start_android_camera(self):
        """Start camera on Android using Kivy camera provider."""
        try:
            from kivy.uix.camera import Camera
            
            self.camera = Camera(
                index=0,
                resolution=(1280, 720),
                play=True,
                size_hint=(1, 1)
            )
            self.camera.bind(on_texture=self._on_camera_frame)
            self.camera_container.add_widget(self.camera)
            
        except Exception as e:
            Logger.error(f"Scanner: Android camera failed: {e}")
            self.message_label.text = "Camera not available"
    
    def _start_desktop_camera(self):
        """Start camera on desktop for testing."""
        try:
            from kivy.uix.camera import Camera
            
            self.camera = Camera(
                index=0,
                resolution=(640, 480),
                play=True,
                size_hint=(1, 1)
            )
            self.camera.bind(on_texture=self._on_camera_frame)
            self.camera_container.add_widget(self.camera)
            
        except Exception as e:
            Logger.warning(f"Scanner: Desktop camera failed: {e}")
            self.message_label.text = "Camera preview unavailable in desktop mode"
    
    def _stop_camera(self):
        """Stop camera preview."""
        if hasattr(self, 'camera') and self.camera:
            self.camera.play = False
            if self.camera.parent:
                self.camera.parent.remove_widget(self.camera)
            self.camera = None
        self.camera_ready = False
    
    def _on_camera_frame(self, camera, texture):
        """Handle camera frame for document detection."""
        if not self.pipeline or not texture:
            return
        
        # Throttled detection in pipeline handles frame rate
        # For now, we'll detect on capture only to save resources
    
    def _draw_quad_overlay(self, quad: QuadResult):
        """Draw document quad overlay on preview."""
        self.overlay.canvas.clear()
        
        if not quad.is_valid:
            return
        
        with self.overlay.canvas:
            Color(*self.theme.get_color('overlay'))
            
            # Scale points to overlay size
            scale_x = self.overlay.width / quad.frame_size[0]
            scale_y = self.overlay.height / quad.frame_size[1]
            
            points = []
            for x, y in quad.points:
                # Flip Y coordinate (camera coords vs screen coords)
                screen_x = x * scale_x
                screen_y = self.overlay.height - (y * scale_y)
                points.extend([screen_x, screen_y])
            
            # Close the quad
            points.extend(points[:2])
            
            Line(points=points, width=3)
    
    def _on_capture(self, *args):
        """Capture current frame."""
        if not self.camera_ready:
            return
        
        # Check page limit
        app = App.get_running_app()
        max_pages = 200
        if app and app.app_state_repo:
            state = app.app_state_repo.get_app_state()
            if state:
                max_pages = state.max_pages_per_document
        
        if self.session and len(self.session.pages) >= max_pages:
            self.message_label.text = f"Maximum {max_pages} pages reached"
            Clock.schedule_once(lambda dt: setattr(self.message_label, 'text', ''), 3)
            return
        
        self.message_label.text = "Capturing..."
        
        try:
            # Capture image from camera
            if hasattr(self, 'camera') and self.camera and self.camera.texture:
                # Save camera texture to file
                import time
                cache_path = app.get_cache_path() if app else '/tmp'
                timestamp = int(time.time() * 1000)
                capture_path = os.path.join(cache_path, f"capture_{timestamp}.jpg")
                
                self.camera.export_to_png(capture_path)  # Actually saves as PNG
                
                # Create session if needed
                if self.session is None:
                    self.session = ScanSession()
                
                # Detect document and go to crop screen
                self._process_capture(capture_path)
        except Exception as e:
            Logger.error(f"Scanner: Capture failed: {e}")
            self.message_label.text = f"Capture failed: {e}"
            Clock.schedule_once(lambda dt: setattr(self.message_label, 'text', ''), 3)
    
    def _process_capture(self, image_path: str):
        """Process captured image and navigate to crop screen."""
        # Detect document quad
        if self.pipeline:
            quad = self.pipeline.detect_document(image_path)
        else:
            quad = QuadResult(detected=False)
        
        # Store for crop screen
        self.manager.get_screen('crop_adjust').set_image(
            image_path=image_path,
            quad_result=quad,
            session=self.session,
            page_index=len(self.session.pages) if self.session else 0
        )
        
        self.message_label.text = ''
        self.manager.current = 'crop_adjust'
    
    def _on_flash_toggle(self, *args):
        """Toggle flash."""
        self.flash_on = not self.flash_on
        self.flash_btn.text = '⚡' if not self.flash_on else '🔦'
        
        # Toggle actual flash (platform-specific)
        if platform == 'android' and hasattr(self, 'camera') and self.camera:
            try:
                # This is simplified - actual implementation needs camera2 API
                Logger.info(f"Scanner: Flash {'on' if self.flash_on else 'off'}")
            except:
                pass
    
    def _on_preview(self, *args):
        """Show captured pages preview."""
        if self.session and self.session.pages:
            # Navigate to export with current session
            export_screen = self.manager.get_screen('export')
            export_screen.set_session(self.session)
            self.manager.current = 'export'
    
    def _on_done(self, *args):
        """Complete scanning session."""
        if self.session and self.session.pages:
            export_screen = self.manager.get_screen('export')
            export_screen.set_session(self.session)
            self.manager.current = 'export'
    
    def _on_back(self, *args):
        """Go back to home."""
        self.save_session()
        self.manager.current = 'home'
    
    def _update_page_count(self):
        """Update page counter display."""
        if self.session:
            self.page_counter.current = len(self.session.pages) - 1 if self.session.pages else 0
            self.page_counter.total = len(self.session.pages)
            self.done_btn.disabled = len(self.session.pages) == 0
        else:
            self.page_counter.current = 0
            self.page_counter.total = 0
            self.done_btn.disabled = True
    
    def add_page(self, page: Page):
        """Add a processed page to the session."""
        if self.session is None:
            self.session = ScanSession()
        
        self.session.add_page(page)
        self._update_page_count()
        self.save_session()
        Logger.info(f"Scanner: Added page {len(self.session.pages)}")
    
    def restore_session(self, session: ScanSession):
        """Restore a previous session."""
        self.session = session
        self._update_page_count()
        Logger.info(f"Scanner: Restored session with {len(session.pages)} pages")
    
    def save_session(self):
        """Save current session for process death recovery."""
        if self.session and self.session.pages:
            app = App.get_running_app()
            if app and app.session_store:
                app.session_store.save_session(self.session)
                Logger.info("Scanner: Session saved")
    
    def clear_session(self):
        """Clear the current session."""
        self.session = None
        self._update_page_count()
