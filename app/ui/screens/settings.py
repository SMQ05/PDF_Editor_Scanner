"""
Settings Screen for PDF Scanner App.
Remove Ads purchase, restore purchases, and privacy policy.
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
from app.ui.widgets import RoundedButton


class SettingsScreen(Screen):
    """Settings screen with Remove Ads and privacy policy."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = get_theme()
        self._build_ui()
    
    def _build_ui(self):
        """Build the settings screen UI."""
        root = BoxLayout(orientation='vertical', padding=16, spacing=0)
        
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
            text='Settings',
            font_size='22sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            valign='middle',
            bold=True
        )
        title.bind(size=lambda *x: setattr(title, 'text_size', (title.width, None)))
        header.add_widget(title)
        
        root.add_widget(header)
        
        # Content scroll
        content_scroll = ScrollView()
        
        content = BoxLayout(
            orientation='vertical',
            spacing=24,
            padding=[0, 24],
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))
        
        # Remove Ads section
        ads_section = self._create_section(
            "Remove Ads",
            "Remove all advertisements from the app with a one-time purchase."
        )
        
        self.ads_status = Label(
            text='Loading...',
            font_size='14sp',
            color=self.theme.get_color('on_surface_variant'),
            halign='left',
            size_hint_y=None,
            height=24
        )
        self.ads_status.bind(size=lambda *x: setattr(self.ads_status, 'text_size', (self.ads_status.width, None)))
        ads_section.add_widget(self.ads_status)
        
        ads_buttons = BoxLayout(size_hint_y=None, height=48, spacing=12)
        
        self.purchase_btn = RoundedButton(
            text='Purchase Remove Ads',
            variant='primary'
        )
        self.purchase_btn.bind(on_release=self._on_purchase)
        ads_buttons.add_widget(self.purchase_btn)
        
        self.restore_btn = RoundedButton(
            text='Restore',
            variant='outline',
            size_hint_x=0.4
        )
        self.restore_btn.bind(on_release=self._on_restore)
        ads_buttons.add_widget(self.restore_btn)
        
        ads_section.add_widget(ads_buttons)
        content.add_widget(ads_section)
        
        # Max pages setting
        pages_section = self._create_section(
            "Maximum Pages",
            "Maximum number of pages allowed per document scan session."
        )
        
        self.pages_label = Label(
            text='200 pages',
            font_size='16sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            size_hint_y=None,
            height=30
        )
        self.pages_label.bind(size=lambda *x: setattr(self.pages_label, 'text_size', (self.pages_label.width, None)))
        pages_section.add_widget(self.pages_label)
        
        content.add_widget(pages_section)
        
        # Privacy policy
        privacy_section = self._create_section(
            "Privacy Policy",
            "Learn how we handle your data and protect your privacy."
        )
        
        privacy_btn = RoundedButton(
            text='View Privacy Policy',
            variant='outline',
            size_hint_y=None,
            height=48
        )
        privacy_btn.bind(on_release=self._on_privacy)
        privacy_section.add_widget(privacy_btn)
        
        content.add_widget(privacy_section)
        
        # About section
        about_section = self._create_section(
            "About",
            ""
        )
        
        version_label = Label(
            text='PDF Scanner v1.0.0',
            font_size='14sp',
            color=self.theme.get_color('on_surface_variant'),
            halign='left',
            size_hint_y=None,
            height=24
        )
        version_label.bind(size=lambda *x: setattr(version_label, 'text_size', (version_label.width, None)))
        about_section.add_widget(version_label)
        
        content.add_widget(about_section)
        
        content.add_widget(Widget())  # Spacer
        
        content_scroll.add_widget(content)
        root.add_widget(content_scroll)
        
        self.add_widget(root)
        self.root_layout = root
    
    def _create_section(self, title: str, description: str) -> BoxLayout:
        """Create a settings section with title and description."""
        section = BoxLayout(
            orientation='vertical',
            spacing=8,
            size_hint_y=None
        )
        section.bind(minimum_height=section.setter('height'))
        
        title_label = Label(
            text=title,
            font_size='18sp',
            color=self.theme.get_color('on_surface'),
            halign='left',
            bold=True,
            size_hint_y=None,
            height=28
        )
        title_label.bind(size=lambda *x: setattr(title_label, 'text_size', (title_label.width, None)))
        section.add_widget(title_label)
        
        if description:
            desc_label = Label(
                text=description,
                font_size='14sp',
                color=self.theme.get_color('on_surface_variant'),
                halign='left',
                size_hint_y=None,
                height=40
            )
            desc_label.bind(size=lambda *x: setattr(desc_label, 'text_size', (desc_label.width, None)))
            section.add_widget(desc_label)
        
        return section
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.root_layout.pos
        self.bg_rect.size = self.root_layout.size
    
    def on_enter(self):
        """Called when screen is shown."""
        self._update_ads_status()
        self._update_pages_setting()
    
    def _update_ads_status(self):
        """Update the ads status display."""
        app = App.get_running_app()
        
        if app and app.ads_manager:
            if app.ads_manager.app_state.ads_removed_purchased:
                self.ads_status.text = "✓ Ads removed - Thank you!"
                self.ads_status.color = self.theme.get_color('success')
                self.purchase_btn.disabled = True
                self.purchase_btn.text = "Purchased"
            else:
                self.ads_status.text = "Ads are currently enabled"
                self.ads_status.color = self.theme.get_color('on_surface_variant')
                self.purchase_btn.disabled = False
                self.purchase_btn.text = "Purchase Remove Ads"
        else:
            self.ads_status.text = "Billing unavailable"
    
    def _update_pages_setting(self):
        """Update max pages display."""
        app = App.get_running_app()
        
        if app and app.app_state_repo:
            state = app.app_state_repo.get_app_state()
            if state:
                self.pages_label.text = f"{state.max_pages_per_document} pages"
    
    def _on_purchase(self, *args):
        """Handle Remove Ads purchase."""
        app = App.get_running_app()
        
        if not app or not app.ads_manager:
            return
        
        self.purchase_btn.disabled = True
        self.purchase_btn.text = "Processing..."
        
        def on_result(success: bool, message: str):
            if success:
                self.ads_status.text = "✓ Purchase successful! Ads removed."
                self.ads_status.color = self.theme.get_color('success')
                self.purchase_btn.text = "Purchased"
                Logger.info("Settings: Purchase successful")
            else:
                self.ads_status.text = f"Purchase failed: {message}"
                self.ads_status.color = self.theme.get_color('error')
                self.purchase_btn.disabled = False
                self.purchase_btn.text = "Purchase Remove Ads"
                Logger.error(f"Settings: Purchase failed: {message}")
        
        app.ads_manager.purchase_remove_ads(on_result)
    
    def _on_restore(self, *args):
        """Handle restore purchases."""
        app = App.get_running_app()
        
        if not app or not app.ads_manager:
            return
        
        self.restore_btn.disabled = True
        self.restore_btn.text = "Restoring..."
        
        def on_result(success: bool, message: str):
            self.restore_btn.disabled = False
            self.restore_btn.text = "Restore"
            
            if success:
                self.ads_status.text = "✓ Purchases restored! Ads removed."
                self.ads_status.color = self.theme.get_color('success')
                self.purchase_btn.disabled = True
                self.purchase_btn.text = "Purchased"
                Logger.info("Settings: Restore successful")
            else:
                self.ads_status.text = message
                self.ads_status.color = self.theme.get_color('on_surface_variant')
                Logger.info(f"Settings: Restore result: {message}")
        
        app.ads_manager.restore_purchases(on_result)
    
    def _on_privacy(self, *args):
        """Open privacy policy."""
        from app.android_bridge.intents import open_url
        
        # Open privacy policy URL
        # Replace with your actual privacy policy URL
        privacy_url = "https://example.com/privacy-policy"
        open_url(privacy_url)
    
    def _on_back(self, *args):
        """Go back to home."""
        self.manager.current = 'home'
