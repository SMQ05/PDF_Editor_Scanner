"""
Scanner Pipeline for PDF Scanner App.
Orchestrates the complete scanning workflow with background processing.
"""
import os
import threading
import time
from typing import Optional, Callable, List, Tuple
from kivy.logger import Logger
from kivy.clock import Clock

from app.domain.models import Page, FilterType, QuadResult, ProcessingResult
from .quad_detect import QuadDetector
from .warp import PerspectiveWarper
from .filters import ImageFilters
from .exif_sanitize import sanitize_image


class ScannerPipeline:
    """Orchestrates document scanning: detect -> warp -> filter -> save."""
    
    # Preview throttling (FPS)
    PREVIEW_FRAME_INTERVAL = 0.2  # 5 FPS for detection
    
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.detector = QuadDetector()
        self.warper = PerspectiveWarper()
        self.filters = ImageFilters()
        
        self._processing_thread: Optional[threading.Thread] = None
        self._is_processing = False
        self._last_preview_time = 0
        
        # Ensure cache directory exists
        os.makedirs(cache_path, exist_ok=True)
    
    def detect_document_preview(self, image_bytes: bytes, width: int, height: int,
                                 callback: Callable[[QuadResult], None]) -> bool:
        """
        Detect document in preview frame (throttled for performance).
        
        Args:
            image_bytes: Raw image bytes from camera
            width: Frame width
            height: Frame height
            callback: Function to call with detection result
            
        Returns:
            True if detection was run, False if throttled
        """
        current_time = time.time()
        if current_time - self._last_preview_time < self.PREVIEW_FRAME_INTERVAL:
            return False
        
        self._last_preview_time = current_time
        
        # Run detection in background
        def detect():
            result = self.detector.detect_from_bytes(image_bytes, width, height)
            Clock.schedule_once(lambda dt: callback(result), 0)
        
        threading.Thread(target=detect, daemon=True).start()
        return True
    
    def detect_document(self, image_path: str) -> QuadResult:
        """
        Detect document in captured image (full quality).
        
        Args:
            image_path: Path to captured image
            
        Returns:
            QuadResult with detection info
        """
        return self.detector.detect(image_path)
    
    def process_capture(self, image_path: str, quad_points: Optional[List[Tuple[int, int]]] = None,
                        filter_type: FilterType = FilterType.ORIGINAL,
                        rotation: int = 0,
                        progress_callback: Callable[[str], None] = None) -> ProcessingResult:
        """
        Process a captured image: warp, rotate, filter, sanitize.
        
        Args:
            image_path: Path to captured image
            quad_points: Quad corners for perspective correction (or None for no warp)
            filter_type: Filter to apply
            rotation: Degrees to rotate (0, 90, 180, 270)
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProcessingResult with output path
        """
        result = ProcessingResult()
        start_time = time.time()
        
        try:
            current_path = image_path
            
            # Step 1: Perspective warp (if quad provided)
            if progress_callback:
                Clock.schedule_once(lambda dt: progress_callback("Correcting perspective..."), 0)
            
            if quad_points:
                timestamp = int(time.time() * 1000)
                warped_path = os.path.join(self.cache_path, f"warped_{timestamp}.jpg")
                current_path = self.warper.warp(current_path, quad_points, warped_path)
            
            # Step 2: Rotation
            if rotation != 0:
                if progress_callback:
                    Clock.schedule_once(lambda dt: progress_callback("Rotating..."), 0)
                
                timestamp = int(time.time() * 1000)
                rotated_path = os.path.join(self.cache_path, f"rotated_{timestamp}.jpg")
                current_path = self.warper.rotate_image(current_path, rotation, rotated_path)
            
            # Step 3: Auto-deskew (optional, light skew correction)
            if quad_points:  # Only deskew warped images
                if progress_callback:
                    Clock.schedule_once(lambda dt: progress_callback("Deskewing..."), 0)
                
                timestamp = int(time.time() * 1000)
                deskewed_path = os.path.join(self.cache_path, f"deskewed_{timestamp}.jpg")
                current_path = self.warper.deskew(current_path, deskewed_path)
            
            # Step 4: Apply filter
            if filter_type != FilterType.ORIGINAL:
                if progress_callback:
                    Clock.schedule_once(lambda dt: progress_callback("Applying filter..."), 0)
                
                timestamp = int(time.time() * 1000)
                filtered_path = os.path.join(self.cache_path, f"filtered_{timestamp}.jpg")
                current_path = self.filters.apply_filter(current_path, filter_type, filtered_path)
            
            # Step 5: Sanitize (remove EXIF)
            if progress_callback:
                Clock.schedule_once(lambda dt: progress_callback("Finalizing..."), 0)
            
            timestamp = int(time.time() * 1000)
            final_path = os.path.join(self.cache_path, f"page_{timestamp}.jpg")
            current_path = sanitize_image(current_path, final_path)
            
            result.success = True
            result.output_path = current_path
            
        except Exception as e:
            Logger.error(f"Pipeline: Processing failed: {e}")
            result.error_message = str(e)
        
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        Logger.info(f"Pipeline: Processed in {result.processing_time_ms}ms")
        return result
    
    def process_capture_async(self, image_path: str, 
                               quad_points: Optional[List[Tuple[int, int]]] = None,
                               filter_type: FilterType = FilterType.ORIGINAL,
                               rotation: int = 0,
                               progress_callback: Callable[[str], None] = None,
                               completion_callback: Callable[[ProcessingResult], None] = None):
        """
        Process capture in background thread.
        
        Args:
            Same as process_capture, plus completion_callback
        """
        if self._is_processing:
            Logger.warning("Pipeline: Already processing")
            if completion_callback:
                result = ProcessingResult(error_message="Already processing")
                Clock.schedule_once(lambda dt: completion_callback(result), 0)
            return
        
        self._is_processing = True
        
        def process():
            result = self.process_capture(
                image_path, quad_points, filter_type, rotation, progress_callback
            )
            self._is_processing = False
            if completion_callback:
                Clock.schedule_once(lambda dt: completion_callback(result), 0)
        
        self._processing_thread = threading.Thread(target=process, daemon=True)
        self._processing_thread.start()
    
    def is_low_light(self, image_path: str) -> bool:
        """Check if image is in low light conditions."""
        return self.detector.is_low_light(image_path)
    
    def get_fallback_quad(self, width: int, height: int) -> List[Tuple[int, int]]:
        """Get full-frame quad for manual crop fallback."""
        return self.detector.get_full_frame_quad(width, height)
    
    def cleanup_temp_files(self, keep_paths: List[str] = None):
        """
        Clean up temporary processing files.
        
        Args:
            keep_paths: List of paths to keep (not delete)
        """
        keep_set = set(keep_paths) if keep_paths else set()
        
        try:
            for filename in os.listdir(self.cache_path):
                filepath = os.path.join(self.cache_path, filename)
                if filepath not in keep_set:
                    # Only delete processing temp files
                    if any(prefix in filename for prefix in ['warped_', 'rotated_', 
                                                              'deskewed_', 'filtered_',
                                                              'sanitized_']):
                        try:
                            os.remove(filepath)
                        except:
                            pass
            Logger.info("Pipeline: Cleaned up temp files")
        except Exception as e:
            Logger.error(f"Pipeline: Cleanup failed: {e}")
    
    def create_thumbnail(self, image_path: str, max_size: int = 150) -> str:
        """
        Create thumbnail for page preview.
        
        Args:
            image_path: Path to full image
            max_size: Maximum dimension for thumbnail
            
        Returns:
            Path to thumbnail
        """
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            base = os.path.splitext(os.path.basename(image_path))[0]
            thumb_path = os.path.join(self.cache_path, f"thumb_{base}.jpg")
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(thumb_path, 'JPEG', quality=80)
            
            return thumb_path
        except Exception as e:
            Logger.error(f"Pipeline: Thumbnail creation failed: {e}")
            return image_path
