"""
AdMob Bridge for PDF Scanner App.
Python wrapper for native AdMob functionality.
"""
from typing import Callable, Optional
from kivy.logger import Logger
from kivy.clock import Clock

from .jnius_api import is_android, get_activity, get_bridge_class


class AdMobBridge:
    """
    Bridge to native AdMob functionality.
    Manages banner and interstitial ads.
    """
    
    # Test ad unit IDs - replace with production IDs
    BANNER_ID = "ca-app-pub-3940256099942544/6300978111"  # Test banner
    INTERSTITIAL_ID = "ca-app-pub-3940256099942544/1033173712"  # Test interstitial
    
    def __init__(self):
        self._initialized = False
        self._banner_visible = False
        self._interstitial_loaded = False
        self._interstitial_callback: Optional[Callable] = None
        self._admob_manager = None
        
        if is_android():
            self._init_native()
    
    def _init_native(self):
        """Initialize native AdMob components."""
        try:
            self._admob_manager = get_bridge_class('AdMobManager')
            
            if self._admob_manager:
                activity = get_activity()
                if activity:
                    self._admob_manager.initialize(activity)
                    self._initialized = True
                    Logger.info("AdMob: Initialized successfully")
        except Exception as e:
            Logger.error(f"AdMob: Initialization failed: {e}")
    
    def show_banner(self):
        """Show the banner ad at the bottom of the screen."""
        if not self._initialized or not is_android():
            return
        
        try:
            activity = get_activity()
            if activity and self._admob_manager:
                self._admob_manager.showBanner(activity, self.BANNER_ID)
                self._banner_visible = True
                Logger.info("AdMob: Banner shown")
        except Exception as e:
            Logger.error(f"AdMob: Show banner failed: {e}")
    
    def hide_banner(self):
        """Hide the banner ad."""
        if not self._initialized or not is_android():
            return
        
        try:
            if self._admob_manager:
                self._admob_manager.hideBanner()
                self._banner_visible = False
                Logger.info("AdMob: Banner hidden")
        except Exception as e:
            Logger.error(f"AdMob: Hide banner failed: {e}")
    
    def load_interstitial(self):
        """Pre-load an interstitial ad."""
        if not self._initialized or not is_android():
            return
        
        try:
            activity = get_activity()
            if activity and self._admob_manager:
                self._admob_manager.loadInterstitial(activity, self.INTERSTITIAL_ID)
                Logger.info("AdMob: Loading interstitial")
        except Exception as e:
            Logger.error(f"AdMob: Load interstitial failed: {e}")
    
    def is_interstitial_ready(self) -> bool:
        """Check if interstitial is loaded and ready."""
        if not self._initialized or not is_android():
            return False
        
        try:
            if self._admob_manager:
                return self._admob_manager.isInterstitialReady()
        except Exception as e:
            Logger.error(f"AdMob: Check interstitial failed: {e}")
        
        return False
    
    def show_interstitial(self, on_closed: Callable = None):
        """
        Show interstitial ad if loaded.
        
        Args:
            on_closed: Callback when ad is closed
        """
        if not self._initialized or not is_android():
            if on_closed:
                on_closed()
            return
        
        self._interstitial_callback = on_closed
        
        try:
            activity = get_activity()
            if activity and self._admob_manager:
                if self._admob_manager.isInterstitialReady():
                    self._admob_manager.showInterstitial(activity)
                    Logger.info("AdMob: Interstitial shown")
                    
                    # Schedule callback check (ad manager calls back via static method)
                    self._poll_interstitial_closed()
                else:
                    Logger.info("AdMob: Interstitial not ready")
                    if on_closed:
                        on_closed()
        except Exception as e:
            Logger.error(f"AdMob: Show interstitial failed: {e}")
            if on_closed:
                on_closed()
    
    def _poll_interstitial_closed(self, attempts: int = 0):
        """Poll for interstitial closed state."""
        if attempts > 60:  # Max 30 seconds
            if self._interstitial_callback:
                self._interstitial_callback()
                self._interstitial_callback = None
            return
        
        try:
            if self._admob_manager and self._admob_manager.wasInterstitialClosed():
                if self._interstitial_callback:
                    self._interstitial_callback()
                    self._interstitial_callback = None
                # Reload next interstitial
                self.load_interstitial()
                return
        except:
            pass
        
        # Continue polling
        Clock.schedule_once(lambda dt: self._poll_interstitial_closed(attempts + 1), 0.5)
    
    @property
    def is_banner_visible(self) -> bool:
        """Check if banner is currently visible."""
        return self._banner_visible


# Fallback for non-Android testing
class MockAdMobBridge:
    """Mock AdMob bridge for testing on non-Android platforms."""
    
    def __init__(self):
        self._banner_visible = False
        Logger.info("AdMob: Using mock bridge (not on Android)")
    
    def show_banner(self):
        self._banner_visible = True
        Logger.info("AdMob (mock): Banner shown")
    
    def hide_banner(self):
        self._banner_visible = False
        Logger.info("AdMob (mock): Banner hidden")
    
    def load_interstitial(self):
        Logger.info("AdMob (mock): Loading interstitial")
    
    def is_interstitial_ready(self) -> bool:
        return True
    
    def show_interstitial(self, on_closed: Callable = None):
        Logger.info("AdMob (mock): Interstitial shown")
        if on_closed:
            Clock.schedule_once(lambda dt: on_closed(), 1.0)
    
    @property
    def is_banner_visible(self) -> bool:
        return self._banner_visible
