"""
Custom widgets for PDF Scanner App.
Reusable UI components.
"""
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.properties import (
    StringProperty, ListProperty, NumericProperty, 
    BooleanProperty, ObjectProperty
)
from kivy.animation import Animation

from .theme import get_theme


class RoundedButton(Button):
    """Button with rounded corners and theme colors."""
    
    bg_color = ListProperty([0.4, 0.2, 0.8, 1])
    text_color = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(12)
    
    def __init__(self, variant='primary', **kwargs):
        super().__init__(**kwargs)
        theme = get_theme()
        
        if variant == 'primary':
            self.bg_color = theme.get_color('primary')
            self.text_color = theme.get_color('on_primary')
        elif variant == 'secondary':
            self.bg_color = theme.get_color('secondary_container')
            self.text_color = theme.get_color('on_surface')
        elif variant == 'outline':
            self.bg_color = [0, 0, 0, 0]
            self.text_color = theme.get_color('primary')
        
        self.color = self.text_color
        self.background_color = [0, 0, 0, 0]
        self.background_normal = ''
        
        self.bind(size=self._update_canvas, pos=self._update_canvas)
        self._update_canvas()
    
    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
    
    def on_press(self):
        # Subtle press animation
        anim = Animation(opacity=0.7, duration=0.05)
        anim.start(self)
    
    def on_release(self):
        anim = Animation(opacity=1.0, duration=0.1)
        anim.start(self)


class DocumentCard(BoxLayout):
    """Card widget for displaying a document in the recents list."""
    
    doc_name = StringProperty('')
    doc_date = StringProperty('')
    doc_pages = NumericProperty(0)
    doc_size = StringProperty('')
    thumbnail_path = StringProperty('')
    
    def __init__(self, document=None, on_tap=None, on_long_press=None, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 80)
        kwargs.setdefault('padding', 8)
        kwargs.setdefault('spacing', 12)
        super().__init__(**kwargs)
        
        self.document = document
        self.on_tap_callback = on_tap
        self.on_long_press_callback = on_long_press
        
        if document:
            self.doc_name = document.name
            self.doc_date = document.created_at.strftime('%b %d, %Y')
            self.doc_pages = document.page_count
            self.doc_size = self._format_size(document.file_size)
            self.thumbnail_path = document.thumbnail_path
        
        self._build_ui()
        self.bind(size=self._update_bg, pos=self._update_bg)
        self._update_bg()
    
    def _build_ui(self):
        theme = get_theme()
        
        # Thumbnail
        thumb_container = Widget(size_hint=(None, None), size=(60, 60))
        self.add_widget(thumb_container)
        
        # Info section
        info_box = BoxLayout(orientation='vertical', spacing=4)
        
        name_label = Label(
            text=self.doc_name,
            font_size='16sp',
            color=theme.get_color('on_surface'),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=24
        )
        name_label.bind(size=lambda *x: setattr(name_label, 'text_size', (name_label.width, None)))
        
        meta_label = Label(
            text=f"{self.doc_pages} pages • {self.doc_size} • {self.doc_date}",
            font_size='12sp',
            color=theme.get_color('on_surface_variant'),
            halign='left',
            valign='top',
            size_hint_y=None,
            height=20
        )
        meta_label.bind(size=lambda *x: setattr(meta_label, 'text_size', (meta_label.width, None)))
        
        info_box.add_widget(name_label)
        info_box.add_widget(meta_label)
        info_box.add_widget(Widget())  # Spacer
        
        self.add_widget(info_box)
    
    def _update_bg(self, *args):
        theme = get_theme()
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme.get_color('surface_variant'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
    
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.collide_point(*touch.pos):
                if self.on_tap_callback:
                    self.on_tap_callback(self.document)
            return True
        return super().on_touch_up(touch)


class CornerHandle(Widget):
    """Draggable corner handle for manual crop adjustment."""
    
    corner_index = NumericProperty(0)  # 0=TL, 1=TR, 2=BR, 3=BL
    handle_color = ListProperty([0.4, 0.2, 0.8, 1])
    handle_radius = NumericProperty(20)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (self.handle_radius * 2, self.handle_radius * 2)
        
        theme = get_theme()
        self.handle_color = theme.get_color('corner_handle')
        
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self._update_canvas()
    
    def _update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Outer circle
            Color(*self.handle_color)
            Ellipse(
                pos=self.pos, 
                size=self.size
            )
            # Inner circle (white)
            Color(1, 1, 1, 1)
            inner_margin = 6
            Ellipse(
                pos=(self.x + inner_margin, self.y + inner_margin),
                size=(self.width - inner_margin * 2, self.height - inner_margin * 2)
            )
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.center = touch.pos
            # Dispatch custom event for parent to update quad
            self.dispatch('on_corner_move')
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)
    
    def on_corner_move(self):
        """Called when corner is moved."""
        pass


# Register events
CornerHandle.register_event_type('on_corner_move')


class FilterChip(BoxLayout):
    """Filter selection chip for image filters."""
    
    filter_name = StringProperty('')
    is_selected = BooleanProperty(False)
    preview_image = ObjectProperty(None)
    
    def __init__(self, filter_type=None, on_select=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (80, 100))
        kwargs.setdefault('padding', 4)
        kwargs.setdefault('spacing', 4)
        super().__init__(**kwargs)
        
        self.filter_type = filter_type
        self.on_select_callback = on_select
        
        if filter_type:
            self.filter_name = filter_type.value.replace('_', ' ').title()
        
        self._build_ui()
        self.bind(is_selected=self._update_selection)
        self._update_bg()
    
    def _build_ui(self):
        theme = get_theme()
        
        # Preview area
        preview_container = Widget(size_hint=(1, None), height=60)
        self.add_widget(preview_container)
        
        # Label
        label = Label(
            text=self.filter_name,
            font_size='11sp',
            color=theme.get_color('on_surface'),
            size_hint_y=None,
            height=20
        )
        self.add_widget(label)
        
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _update_bg(self, *args):
        theme = get_theme()
        bg_color = theme.get_color('primary_container') if self.is_selected else theme.get_color('surface_variant')
        
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            
            if self.is_selected:
                Color(*theme.get_color('primary'))
                Line(
                    rounded_rectangle=(self.x, self.y, self.width, self.height, 8),
                    width=2
                )
    
    def _update_selection(self, *args):
        self._update_bg()
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_selected = True
            if self.on_select_callback:
                self.on_select_callback(self.filter_type)
            return True
        return super().on_touch_down(touch)


class PageCounter(Label):
    """Counter showing current page in scan session."""
    
    current = NumericProperty(0)
    total = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '14sp'
        theme = get_theme()
        self.color = theme.get_color('on_surface')
        self.bind(current=self._update_text, total=self._update_text)
        self._update_text()
    
    def _update_text(self, *args):
        self.text = f"Page {self.current + 1}" if self.total == 0 else f"{self.current + 1}/{self.total}"


class LoadingSpinner(Widget):
    """Simple loading indicator."""
    
    spinning = BooleanProperty(True)
    color = ListProperty([0.4, 0.2, 0.8, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (40, 40)
        
        theme = get_theme()
        self.color = theme.get_color('primary')
        
        self._angle = 0
        self.bind(spinning=self._on_spinning_change)
        self._start_animation()
    
    def _on_spinning_change(self, *args):
        if self.spinning:
            self._start_animation()
    
    def _start_animation(self):
        if self.spinning:
            anim = Animation(_angle=360, duration=1)
            anim.bind(on_complete=lambda *x: self._restart_animation())
            anim.start(self)
            self._draw()
    
    def _restart_animation(self):
        self._angle = 0
        if self.spinning:
            self._start_animation()
    
    def _draw(self):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            # Draw arc (simplified spinner)
            Line(
                circle=(self.center_x, self.center_y, 15, self._angle, self._angle + 270),
                width=3
            )
