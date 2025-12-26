"""
Android Intents Bridge for PDF Scanner App.
Handles sharing files and opening system screens.
"""
import os
from typing import Optional
from kivy.logger import Logger

from .jnius_api import is_android, get_activity, get_java_class, get_bridge_class


def share_file(file_path: str, mime_type: str = "application/pdf",
               title: str = "Share") -> bool:
    """
    Share a file using Android's share sheet.
    
    Args:
        file_path: Absolute path to file to share
        mime_type: MIME type of the file
        title: Title for share chooser
        
    Returns:
        True if share intent was launched
    """
    if not is_android():
        Logger.info(f"Intents (mock): Share file {file_path}")
        return True
    
    try:
        intent_utils = get_bridge_class('IntentUtils')
        activity = get_activity()
        
        if intent_utils and activity:
            intent_utils.shareFile(activity, file_path, mime_type, title)
            Logger.info(f"Intents: Shared file {file_path}")
            return True
        else:
            # Fallback to direct intent creation
            return _share_file_direct(file_path, mime_type, title)
            
    except Exception as e:
        Logger.error(f"Intents: Share failed: {e}")
        return False


def _share_file_direct(file_path: str, mime_type: str, title: str) -> bool:
    """Direct share implementation using pyjnius."""
    try:
        from jnius import autoclass, cast
        
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')
        FileProvider = autoclass('androidx.core.content.FileProvider')
        
        activity = get_activity()
        if not activity:
            return False
        
        context = activity.getApplicationContext()
        
        # Create file URI using FileProvider
        java_file = File(file_path)
        authority = context.getPackageName() + ".fileprovider"
        content_uri = FileProvider.getUriForFile(context, authority, java_file)
        
        # Create share intent
        share_intent = Intent(Intent.ACTION_SEND)
        share_intent.setType(mime_type)
        share_intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', content_uri))
        share_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        
        # Create chooser
        chooser = Intent.createChooser(share_intent, title)
        activity.startActivity(chooser)
        
        Logger.info(f"Intents: Direct share of {file_path}")
        return True
        
    except Exception as e:
        Logger.error(f"Intents: Direct share failed: {e}")
        return False


def open_app_settings() -> bool:
    """
    Open the app's settings screen in Android Settings.
    Used for permission recovery.
    
    Returns:
        True if settings were opened
    """
    if not is_android():
        Logger.info("Intents (mock): Open app settings")
        return True
    
    try:
        intent_utils = get_bridge_class('IntentUtils')
        activity = get_activity()
        
        if intent_utils and activity:
            intent_utils.openAppSettings(activity)
            Logger.info("Intents: Opened app settings")
            return True
        else:
            return _open_settings_direct()
            
    except Exception as e:
        Logger.error(f"Intents: Open settings failed: {e}")
        return False


def _open_settings_direct() -> bool:
    """Direct settings open using pyjnius."""
    try:
        from jnius import autoclass
        
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
        
        activity = get_activity()
        if not activity:
            return False
        
        package_name = activity.getPackageName()
        
        intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
        uri = Uri.fromParts("package", package_name, None)
        intent.setData(uri)
        
        activity.startActivity(intent)
        Logger.info("Intents: Direct open settings")
        return True
        
    except Exception as e:
        Logger.error(f"Intents: Direct settings open failed: {e}")
        return False


def open_url(url: str) -> bool:
    """
    Open a URL in the default browser.
    
    Args:
        url: URL to open
        
    Returns:
        True if browser was opened
    """
    if not is_android():
        Logger.info(f"Intents (mock): Open URL {url}")
        import webbrowser
        webbrowser.open(url)
        return True
    
    try:
        from jnius import autoclass
        
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        
        activity = get_activity()
        if not activity:
            return False
        
        intent = Intent(Intent.ACTION_VIEW)
        intent.setData(Uri.parse(url))
        activity.startActivity(intent)
        
        Logger.info(f"Intents: Opened URL {url}")
        return True
        
    except Exception as e:
        Logger.error(f"Intents: Open URL failed: {e}")
        return False


def request_camera_permission(callback=None) -> bool:
    """
    Request camera permission using Android permission system.
    
    Args:
        callback: Optional callback when permission is granted/denied
        
    Returns:
        True if permission already granted
    """
    if not is_android():
        Logger.info("Intents (mock): Camera permission requested")
        if callback:
            callback(True)
        return True
    
    try:
        from android.permissions import request_permissions, Permission, check_permission
        
        if check_permission(Permission.CAMERA):
            Logger.info("Intents: Camera permission already granted")
            if callback:
                callback(True)
            return True
        
        def on_permission_result(permissions, grants):
            granted = all(grants)
            Logger.info(f"Intents: Camera permission {'granted' if granted else 'denied'}")
            if callback:
                callback(granted)
        
        request_permissions([Permission.CAMERA], on_permission_result)
        return False
        
    except Exception as e:
        Logger.error(f"Intents: Camera permission request failed: {e}")
        if callback:
            callback(False)
        return False


def check_camera_permission() -> bool:
    """Check if camera permission is granted."""
    if not is_android():
        return True
    
    try:
        from android.permissions import check_permission, Permission
        return check_permission(Permission.CAMERA)
    except Exception as e:
        Logger.error(f"Intents: Permission check failed: {e}")
        return False


def is_permission_denied_permanently() -> bool:
    """
    Check if camera permission was denied with "Don't ask again".
    
    Returns:
        True if permission was permanently denied
    """
    if not is_android():
        return False
    
    try:
        from jnius import autoclass
        
        ActivityCompat = autoclass('androidx.core.app.ActivityCompat')
        Manifest = autoclass('android.Manifest$permission')
        
        activity = get_activity()
        if not activity:
            return False
        
        # If permission is not granted and we shouldn't show rationale,
        # it means user selected "Don't ask again"
        should_show = ActivityCompat.shouldShowRequestPermissionRationale(
            activity, Manifest.CAMERA
        )
        
        return not should_show and not check_camera_permission()
        
    except Exception as e:
        Logger.error(f"Intents: Permanent denial check failed: {e}")
        return False
