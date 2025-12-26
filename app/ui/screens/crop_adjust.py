"""
Crop Adjust Screen for PDF Scanner App.
Manual crop adjustment with draggable corners and filter preview.
"""
import os
from typing import Optional, List, Tuple
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line, Rectangle
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.app import App

from app.ui.theme import get_theme
from app.ui.widgets import RoundedButton, CornerHandle, FilterChip
from app.domain.models import ScanSession, Page, FilterType, QuadResult


class CropAdjustScreen(Screen):
    """Screen for adjusting crop corners and applying filters."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = get_theme()
        
        self.image_path: Optional[str] = None
        self.quad_result: Optional[QuadResult] = None
        self.session: Optional[ScanSession] = None
        self.page_index: int = 0
        self.current_filter: FilterType = FilterType.ORIGINAL
        self.rotation: int = 0
        self.corner_handles: List[CornerHandle] = []
        self.quad_points: List[Tuple[int, int]] = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the crop adjust screen UI."""
        root = BoxLayout(orientation='vertical', padding=0, spacing=0)
        
        # Top bar
        top_bar = BoxLayout(
            size_hint_y=None,
            height=56,
            padding=[16, 8],
            spacing=8
        )
        with top_bar.canvas.before:
            Color(*self.theme.get_color('surface'))
            self.top_bar_bg = Rectangle(size=top_bar.size)
        top_bar.bind(size=lambda *x: setattr(self.top_bar_bg, 'size', top_bar.size))
        
        # Back/Cancel button
        back_btn = RoundedButton(
            text='✕',
            variant='outline',
            size_hint=(None, None),
            size=(44, 44)
        )
        back_btn.bind(on_release=self._on_cancel)
        top_bar.add_widget(back_btn)
        
        top_bar.add_widget(Widget())  # Spacer
        
        # Title
        title = Label(
            text='Adjust',
            font_size='18sp',
            color=self.theme.get_color('on_surface'),
            bold=True
        )
        top_bar.add_widget(title)
        
        top_bar.add_widget(Widget())  # Spacer
        
        # Rotation buttons
        rotate_left_btn = RoundedButton(
            text='↺',
            variant='outline',
            size_hint=(None, None),
            size=(44, 44)
        )
        rotate_left_btn.bind(on_release=self._on_rotate_left)
        top_bar.add_widget(rotate_left_btn)
        
        rotate_right_btn = RoundedButton(
            text='↻',
            variant='outline',
            size_hint=(None, None),
            size=(44, 44)
        )
        rotate_right_btn.bind(on_release=self._on_rotate_right)
        top_bar.add_widget(rotate_right_btn)
        
        root.add_widget(top_bar)
        
        # Image container with crop overlay
        self.image_container = RelativeLayout()
        with self.image_container.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.img_bg = Rectangle(size=self.image_container.size)
        self.image_container.bind(size=self._update_image_bg)
        
        # Image widget
        self.image_widget = Image(
            allow_stretch=True,
            keep_ratio=True
        )
        self.image_container.add_widget(self.image_widget)
        
        # Crop overlay widget
        self.crop_overlay = Widget()
        self.image_container.add_widget(self.crop_overlay)
        
        # Corner handles (added dynamically)
        self.handles_container = RelativeLayout()
        self.image_container.add_widget(self.handles_container)
        
        root.add_widget(self.image_container)
        
        # Filter selection bar
        filter_bar = BoxLayout(
            size_hint_y=None,
            height=120,
            padding=[8, 8],
            spacing=8
        )
        with filter_bar.canvas.before:
            Color(*self.theme.get_color('surface'))
            self.filter_bar_bg = Rectangle(size=filter_bar.size)
        filter_bar.bind(size=lambda *x: setattr(self.filter_bar_bg, 'size', filter_bar.size))
        
        filter_scroll = ScrollView(
            do_scroll_y=False,
            size_hint_x=1
        )
        
        self.filters_container = BoxLayout(
            orientation='horizontal',
            spacing=8,
            size_hint_x=None
        )
        self.filters_container.bind(minimum_width=self.filters_container.setter('width'))
        
        # Add filter chips
        for filter_type in FilterType:
            chip = FilterChip(
                filter_type=filter_type,
                on_select=self._on_filter_select
            )
            chip.is_selected = (filter_type == self.current_filter)
            self.filters_container.add_widget(chip)
        
        filter_scroll.add_widget(self.filters_container)
        filter_bar.add_widget(filter_scroll)
        
        root.add_widget(filter_bar)
        
        # Bottom action bar
        bottom_bar = BoxLayout(
            size_hint_y=None,
            height=72,
            padding=[16, 12],
            spacing=16
        )
        with bottom_bar.canvas.before:
            Color(*self.theme.get_color('surface'))
            self.bottom_bar_bg = Rectangle(size=bottom_bar.size)
        bottom_bar.bind(size=lambda *x: setattr(self.bottom_bar_bg, 'size', bottom_bar.size))
        
        # Retake button
        retake_btn = RoundedButton(
            text='Retake',
            variant='outline',
            size_hint_x=0.4
        )
        retake_btn.bind(on_release=self._on_retake)
        bottom_bar.add_widget(retake_btn)
        
        # Confirm button
        confirm_btn = RoundedButton(
            text='Confirm',
            variant='primary'
        )
        confirm_btn.bind(on_release=self._on_confirm)
        bottom_bar.add_widget(confirm_btn)
        
        root.add_widget(bottom_bar)
        
        self.add_widget(root)
        self.root_layout = root
    
    def _update_image_bg(self, *args):
        self.img_bg.size = self.image_container.size
    
    def set_image(self, image_path: str, quad_result: QuadResult,
                  session: ScanSession, page_index: int):
        """Set the image to adjust."""
        self.image_path = image_path
        self.quad_result = quad_result
        self.session = session
        self.page_index = page_index
        self.current_filter = FilterType.ORIGINAL
        self.rotation = 0
        
        # Set quad points
        if quad_result.is_valid:
            self.quad_points = list(quad_result.points)
        else:
            # Use full frame fallback
            from PIL import Image as PILImage
            try:
                img = PILImage.open(image_path)
                w, h = img.size
                margin = 20
                self.quad_points = [
                    (margin, margin),
                    (w - margin, margin),
                    (w - margin, h - margin),
                    (margin, h - margin)
                ]
            except:
                self.quad_points = [(20, 20), (780, 20), (780, 580), (20, 580)]
        
        # Update UI
        self._update_image_display()
        Clock.schedule_once(lambda dt: self._create_corner_handles(), 0.1)
    
    def _update_image_display(self):
        """Update the image widget."""
        if self.image_path:
            self.image_widget.source = self.image_path
            self.image_widget.reload()
    
    def _create_corner_handles(self):
        """Create draggable corner handles."""
        self.handles_container.clear_widgets()
        self.corner_handles = []
        
        if not self.quad_points or len(self.quad_points) != 4:
            return
        
        # Get image display rect (accounting for aspect ratio)
        img_rect = self._get_image_display_rect()
        if not img_rect:
            return
        
        img_x, img_y, img_w, img_h = img_rect
        
        # Get original image size
        try:
            from PIL import Image as PILImage
            img = PILImage.open(self.image_path)
            orig_w, orig_h = img.size
        except:
            return
        
        # Create handles at scaled positions
        for i, (qx, qy) in enumerate(self.quad_points):
            # Scale to display coordinates
            screen_x = img_x + (qx / orig_w) * img_w
            screen_y = img_y + img_h - (qy / orig_h) * img_h  # Flip Y
            
            handle = CornerHandle(corner_index=i)
            handle.center = (screen_x, screen_y)
            handle.bind(on_corner_move=self._on_corner_moved)
            
            self.handles_container.add_widget(handle)
            self.corner_handles.append(handle)
        
        self._draw_crop_lines()
    
    def _get_image_display_rect(self) -> Optional[Tuple[float, float, float, float]]:
        """Get the displayed image rectangle (x, y, width, height)."""
        if not self.image_widget.texture:
            return None
        
        # Get image and container sizes
        tex_w, tex_h = self.image_widget.texture.size
        cont_w, cont_h = self.image_container.size
        
        # Calculate display size (keep ratio)
        ratio = min(cont_w / tex_w, cont_h / tex_h)
        disp_w = tex_w * ratio
        disp_h = tex_h * ratio
        
        # Center in container
        disp_x = (cont_w - disp_w) / 2 + self.image_container.x
        disp_y = (cont_h - disp_h) / 2 + self.image_container.y
        
        return (disp_x, disp_y, disp_w, disp_h)
    
    def _on_corner_moved(self, handle):
        """Handle corner movement."""
        img_rect = self._get_image_display_rect()
        if not img_rect:
            return
        
        img_x, img_y, img_w, img_h = img_rect
        
        try:
            from PIL import Image as PILImage
            img = PILImage.open(self.image_path)
            orig_w, orig_h = img.size
        except:
            return
        
        # Convert screen position to image coordinates
        screen_x, screen_y = handle.center
        
        # Clamp to image bounds
        screen_x = max(img_x, min(img_x + img_w, screen_x))
        screen_y = max(img_y, min(img_y + img_h, screen_y))
        handle.center = (screen_x, screen_y)
        
        # Convert to image coordinates
        img_coord_x = int(((screen_x - img_x) / img_w) * orig_w)
        img_coord_y = int(((img_y + img_h - screen_y) / img_h) * orig_h)  # Flip Y
        
        # Update quad points
        idx = handle.corner_index
        self.quad_points[idx] = (img_coord_x, img_coord_y)
        
        self._draw_crop_lines()
    
    def _draw_crop_lines(self):
        """Draw lines connecting corner handles."""
        self.crop_overlay.canvas.clear()
        
        if len(self.corner_handles) != 4:
            return
        
        with self.crop_overlay.canvas:
            Color(*self.theme.get_color('overlay'))
            
            points = []
            for handle in self.corner_handles:
                points.extend(handle.center)
            # Close the quad
            points.extend(self.corner_handles[0].center)
            
            Line(points=points, width=2)
    
    def _on_filter_select(self, filter_type: FilterType):
        """Handle filter selection."""
        self.current_filter = filter_type
        
        # Update filter chips selection
        for child in self.filters_container.children:
            if isinstance(child, FilterChip):
                child.is_selected = (child.filter_type == filter_type)
        
        Logger.info(f"CropAdjust: Selected filter {filter_type.value}")
    
    def _on_rotate_left(self, *args):
        """Rotate image 90° counterclockwise."""
        self.rotation = (self.rotation - 90) % 360
        Logger.info(f"CropAdjust: Rotation = {self.rotation}°")
    
    def _on_rotate_right(self, *args):
        """Rotate image 90° clockwise."""
        self.rotation = (self.rotation + 90) % 360
        Logger.info(f"CropAdjust: Rotation = {self.rotation}°")
    
    def _on_retake(self, *args):
        """Discard and go back to scanner."""
        # Delete the captured image
        if self.image_path and os.path.exists(self.image_path):
            try:
                os.remove(self.image_path)
            except:
                pass
        
        self.manager.current = 'scanner'
    
    def _on_cancel(self, *args):
        """Cancel and go back."""
        self._on_retake()
    
    def _on_confirm(self, *args):
        """Confirm crop and add page to session."""
        if not self.image_path or not self.session:
            return
        
        app = App.get_running_app()
        if not app:
            return
        
        # Process image with pipeline
        from app.infra.imaging.scanner_pipeline import ScannerPipeline
        
        pipeline = ScannerPipeline(app.get_cache_path())
        
        def on_complete(result):
            if result.success:
                # Create page
                page = Page(
                    image_path=result.output_path,
                    quad_points=self.quad_points,
                    filter_applied=self.current_filter,
                    rotation=self.rotation
                )
                
                # Add to session via scanner screen
                scanner_screen = self.manager.get_screen('scanner')
                scanner_screen.add_page(page)
                
                # Go back to scanner for next page
                self.manager.current = 'scanner'
            else:
                Logger.error(f"CropAdjust: Processing failed: {result.error_message}")
        
        # Process asynchronously
        pipeline.process_capture_async(
            image_path=self.image_path,
            quad_points=self.quad_points if self.quad_points else None,
            filter_type=self.current_filter,
            rotation=self.rotation,
            completion_callback=on_complete
        )
