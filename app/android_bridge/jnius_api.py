"""
PyJNIus API utilities for PDF Scanner App.
Provides platform detection and Android context access.
"""
from kivy.utils import platform
from kivy.logger import Logger


def is_android() -> bool:
    """Check if running on Android platform."""
    return platform == 'android'


def get_activity():
    """
    Get the current Android Activity.
    
    Returns:
        PythonActivity instance or None if not on Android
    """
    if not is_android():
        return None
    
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        return PythonActivity.mActivity
    except Exception as e:
        Logger.error(f"JNIus: Failed to get activity: {e}")
        return None


def get_context():
    """
    Get the Android application Context.
    
    Returns:
        Context instance or None if not on Android
    """
    if not is_android():
        return None
    
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        return PythonActivity.mActivity.getApplicationContext()
    except Exception as e:
        Logger.error(f"JNIus: Failed to get context: {e}")
        return None


def run_on_ui_thread(func):
    """
    Decorator to run a function on Android's UI thread.
    
    Args:
        func: Function to run on UI thread
    """
    if not is_android():
        return func
    
    def wrapper(*args, **kwargs):
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread as android_run_on_ui_thread
            
            @android_run_on_ui_thread
            def run():
                return func(*args, **kwargs)
            
            return run()
        except Exception as e:
            Logger.error(f"JNIus: UI thread execution failed: {e}")
            # Fallback to direct execution
            return func(*args, **kwargs)
    
    return wrapper


def get_java_class(class_name: str):
    """
    Get a Java class by fully qualified name.
    
    Args:
        class_name: Full Java class name (e.g., 'android.content.Intent')
        
    Returns:
        Java class or None
    """
    if not is_android():
        return None
    
    try:
        from jnius import autoclass
        return autoclass(class_name)
    except Exception as e:
        Logger.error(f"JNIus: Failed to load class {class_name}: {e}")
        return None


def call_static_method(class_name: str, method_name: str, *args):
    """
    Call a static method on a Java class.
    
    Args:
        class_name: Full Java class name
        method_name: Static method name
        *args: Arguments to pass to the method
        
    Returns:
        Method result or None on error
    """
    cls = get_java_class(class_name)
    if cls is None:
        return None
    
    try:
        method = getattr(cls, method_name)
        return method(*args)
    except Exception as e:
        Logger.error(f"JNIus: Failed to call {class_name}.{method_name}: {e}")
        return None


# Package name for our Java classes
BRIDGE_PACKAGE = 'com.pdfscanner.docscanner'


def get_bridge_class(simple_name: str):
    """
    Get one of our bridge Java classes.
    
    Args:
        simple_name: Simple class name (e.g., 'AdMobManager')
        
    Returns:
        Java class or None
    """
    return get_java_class(f"{BRIDGE_PACKAGE}.{simple_name}")
