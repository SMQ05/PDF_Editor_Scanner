"""
Billing Bridge for PDF Scanner App.
Python wrapper for Google Play Billing.
"""
from typing import Callable, Optional
from kivy.logger import Logger
from kivy.clock import Clock

from .jnius_api import is_android, get_activity, get_bridge_class


class BillingBridge:
    """
    Bridge to Google Play Billing Library.
    Handles Remove Ads in-app purchase.
    """
    
    # Product ID for Remove Ads - set this in Google Play Console
    REMOVE_ADS_SKU = "remove_ads"
    
    def __init__(self):
        self._initialized = False
        self._billing_manager = None
        self._purchase_callback: Optional[Callable] = None
        self._restore_callback: Optional[Callable] = None
        
        if is_android():
            self._init_native()
    
    def _init_native(self):
        """Initialize native billing components."""
        try:
            self._billing_manager = get_bridge_class('BillingManager')
            
            if self._billing_manager:
                activity = get_activity()
                if activity:
                    self._billing_manager.initialize(activity)
                    self._initialized = True
                    Logger.info("Billing: Initialized successfully")
        except Exception as e:
            Logger.error(f"Billing: Initialization failed: {e}")
    
    def purchase_remove_ads(self, callback: Callable[[bool, str], None]):
        """
        Initiate Remove Ads purchase.
        
        Args:
            callback: Function(success: bool, message: str)
        """
        if not self._initialized or not is_android():
            callback(False, "Billing not available")
            return
        
        self._purchase_callback = callback
        
        try:
            activity = get_activity()
            if activity and self._billing_manager:
                self._billing_manager.purchaseRemoveAds(activity, self.REMOVE_ADS_SKU)
                Logger.info("Billing: Purchase flow started")
                
                # Poll for result
                self._poll_purchase_result()
        except Exception as e:
            Logger.error(f"Billing: Purchase failed: {e}")
            callback(False, str(e))
    
    def _poll_purchase_result(self, attempts: int = 0):
        """Poll for purchase result."""
        if attempts > 120:  # Max 60 seconds
            if self._purchase_callback:
                self._purchase_callback(False, "Purchase timed out")
                self._purchase_callback = None
            return
        
        try:
            if self._billing_manager:
                result = self._billing_manager.getLastPurchaseResult()
                if result is not None:
                    success = result.startswith("SUCCESS")
                    message = result[8:] if success else result[6:]  # Strip prefix
                    
                    if self._purchase_callback:
                        self._purchase_callback(success, message)
                        self._purchase_callback = None
                    return
        except:
            pass
        
        # Continue polling
        Clock.schedule_once(lambda dt: self._poll_purchase_result(attempts + 1), 0.5)
    
    def restore_purchases(self, callback: Callable[[bool], None]):
        """
        Restore previous purchases.
        
        Args:
            callback: Function(is_purchased: bool)
        """
        if not self._initialized or not is_android():
            callback(False)
            return
        
        self._restore_callback = callback
        
        try:
            if self._billing_manager:
                self._billing_manager.restorePurchases()
                Logger.info("Billing: Restoring purchases")
                
                # Poll for result
                self._poll_restore_result()
        except Exception as e:
            Logger.error(f"Billing: Restore failed: {e}")
            callback(False)
    
    def _poll_restore_result(self, attempts: int = 0):
        """Poll for restore result."""
        if attempts > 20:  # Max 10 seconds
            if self._restore_callback:
                self._restore_callback(False)
                self._restore_callback = None
            return
        
        try:
            if self._billing_manager:
                result = self._billing_manager.isRemoveAdsPurchased()
                if result is not None:
                    if self._restore_callback:
                        self._restore_callback(result)
                        self._restore_callback = None
                    return
        except:
            pass
        
        Clock.schedule_once(lambda dt: self._poll_restore_result(attempts + 1), 0.5)
    
    def query_purchases(self, callback: Callable[[bool], None]):
        """
        Query current purchase state.
        
        Args:
            callback: Function(is_purchased: bool)
        """
        if not self._initialized or not is_android():
            callback(False)
            return
        
        try:
            if self._billing_manager:
                is_purchased = self._billing_manager.isRemoveAdsPurchased()
                callback(is_purchased if is_purchased is not None else False)
        except Exception as e:
            Logger.error(f"Billing: Query failed: {e}")
            callback(False)
    
    def is_ads_removed(self) -> bool:
        """
        Synchronous check if ads are removed.
        Use query_purchases for async version.
        """
        if not self._initialized or not is_android():
            return False
        
        try:
            if self._billing_manager:
                result = self._billing_manager.isRemoveAdsPurchased()
                return result if result is not None else False
        except:
            pass
        
        return False


# Fallback for non-Android testing
class MockBillingBridge:
    """Mock billing bridge for testing on non-Android platforms."""
    
    def __init__(self):
        self._is_purchased = False
        Logger.info("Billing: Using mock bridge (not on Android)")
    
    def purchase_remove_ads(self, callback: Callable[[bool, str], None]):
        Logger.info("Billing (mock): Simulating purchase")
        self._is_purchased = True
        Clock.schedule_once(lambda dt: callback(True, "Mock purchase successful"), 1.0)
    
    def restore_purchases(self, callback: Callable[[bool], None]):
        Logger.info("Billing (mock): Restoring purchases")
        Clock.schedule_once(lambda dt: callback(self._is_purchased), 0.5)
    
    def query_purchases(self, callback: Callable[[bool], None]):
        callback(self._is_purchased)
    
    def is_ads_removed(self) -> bool:
        return self._is_purchased
