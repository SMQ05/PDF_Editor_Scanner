"""
Document Edge Detection for PDF Scanner App.
Detects document quadrilateral in camera frames.

Supports:
- OpenCV (preferred, if available)
- Pillow fallback (edge detection with simpler heuristics)
"""
from typing import Optional, List, Tuple
from kivy.logger import Logger

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    Logger.info("QuadDetect: OpenCV available")
except ImportError:
    OPENCV_AVAILABLE = False
    Logger.warning("QuadDetect: OpenCV not available, using Pillow fallback")

# Always import Pillow as fallback
from PIL import Image, ImageFilter, ImageOps

from app.domain.models import QuadResult


class QuadDetector:
    """Detects document quadrilateral in images."""
    
    # Parameters for detection
    DOWNSCALE_WIDTH = 960  # Max width for processing
    BLUR_SIZE = 5
    CANNY_LOW = 50
    CANNY_HIGH = 150
    MIN_AREA_RATIO = 0.1  # Min area as ratio of frame
    MAX_AREA_RATIO = 0.95  # Max area as ratio of frame
    APPROX_EPSILON_RATIO = 0.02  # Polygon approximation tolerance
    
    def __init__(self):
        self.use_opencv = OPENCV_AVAILABLE
        self._last_stable_quad = None
        self._stability_count = 0
        self._stability_threshold = 3  # Frames before accepting new quad
    
    def detect(self, image_path: str) -> QuadResult:
        """Detect document quad from image file."""
        try:
            if self.use_opencv:
                return self._detect_opencv(image_path)
            else:
                return self._detect_pillow(image_path)
        except Exception as e:
            Logger.error(f"QuadDetect: Detection failed: {e}")
            return QuadResult(detected=False)
    
    def detect_from_bytes(self, image_bytes: bytes, width: int, height: int) -> QuadResult:
        """Detect document quad from raw image bytes (for live preview)."""
        try:
            if self.use_opencv:
                return self._detect_opencv_bytes(image_bytes, width, height)
            else:
                return self._detect_pillow_bytes(image_bytes, width, height)
        except Exception as e:
            Logger.error(f"QuadDetect: Detection from bytes failed: {e}")
            return QuadResult(detected=False)
    
    def _detect_opencv(self, image_path: str) -> QuadResult:
        """Detect using OpenCV."""
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return QuadResult(detected=False)
        
        return self._process_opencv(img)
    
    def _detect_opencv_bytes(self, image_bytes: bytes, width: int, height: int) -> QuadResult:
        """Detect from raw bytes using OpenCV."""
        # Convert bytes to numpy array
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        # Reshape based on expected format (assuming RGBA or RGB)
        try:
            if len(arr) == width * height * 4:
                img = arr.reshape((height, width, 4))
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif len(arr) == width * height * 3:
                img = arr.reshape((height, width, 3))
            else:
                return QuadResult(detected=False)
        except:
            return QuadResult(detected=False)
        
        return self._process_opencv(img)
    
    def _process_opencv(self, img) -> QuadResult:
        """Process image with OpenCV to find quad."""
        original_height, original_width = img.shape[:2]
        
        # Downscale for processing
        scale = 1.0
        if original_width > self.DOWNSCALE_WIDTH:
            scale = self.DOWNSCALE_WIDTH / original_width
            img = cv2.resize(img, None, fx=scale, fy=scale)
        
        height, width = img.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (self.BLUR_SIZE, self.BLUR_SIZE), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, self.CANNY_LOW, self.CANNY_HIGH)
        
        # Dilate edges to close gaps
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find best quadrilateral
        best_quad = None
        best_area = 0
        frame_area = width * height
        min_area = frame_area * self.MIN_AREA_RATIO
        max_area = frame_area * self.MAX_AREA_RATIO
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue
            
            # Approximate polygon
            epsilon = self.APPROX_EPSILON_RATIO * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Accept only quadrilaterals
            if len(approx) == 4:
                if area > best_area:
                    # Check if convex
                    if cv2.isContourConvex(approx):
                        best_area = area
                        best_quad = approx
        
        if best_quad is not None:
            # Convert to list of points and scale back to original size
            points = []
            for point in best_quad:
                x = int(point[0][0] / scale)
                y = int(point[0][1] / scale)
                points.append((x, y))
            
            # Order points clockwise starting from top-left
            points = self._order_points(points)
            
            confidence = best_area / frame_area
            
            return QuadResult(
                detected=True,
                points=points,
                confidence=confidence,
                frame_size=(original_width, original_height)
            )
        
        return QuadResult(
            detected=False,
            frame_size=(original_width, original_height)
        )
    
    def _detect_pillow(self, image_path: str) -> QuadResult:
        """Detect using Pillow (fallback)."""
        try:
            img = Image.open(image_path)
            return self._process_pillow(img)
        except Exception as e:
            Logger.error(f"QuadDetect: Pillow detection failed: {e}")
            return QuadResult(detected=False)
    
    def _detect_pillow_bytes(self, image_bytes: bytes, width: int, height: int) -> QuadResult:
        """Detect from bytes using Pillow."""
        try:
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            return self._process_pillow(img)
        except Exception as e:
            Logger.error(f"QuadDetect: Pillow bytes detection failed: {e}")
            return QuadResult(detected=False)
    
    def _process_pillow(self, img: Image.Image) -> QuadResult:
        """Process image with Pillow to detect edges."""
        original_width, original_height = img.size
        
        # Downscale for processing
        scale = 1.0
        if original_width > self.DOWNSCALE_WIDTH:
            scale = self.DOWNSCALE_WIDTH / original_width
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        width, height = img.size
        
        # Convert to grayscale
        gray = img.convert('L')
        
        # Apply edge detection
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # Threshold to binary
        threshold = 30
        edges = edges.point(lambda x: 255 if x > threshold else 0)
        
        # Simple heuristic: find bounding box of edge pixels
        # This is a simplified fallback - detects document region roughly
        bbox = self._find_content_bbox(edges)
        
        if bbox:
            x1, y1, x2, y2 = bbox
            # Scale back to original size
            points = [
                (int(x1 / scale), int(y1 / scale)),  # top-left
                (int(x2 / scale), int(y1 / scale)),  # top-right
                (int(x2 / scale), int(y2 / scale)),  # bottom-right
                (int(x1 / scale), int(y2 / scale)),  # bottom-left
            ]
            
            return QuadResult(
                detected=True,
                points=points,
                confidence=0.5,  # Lower confidence for Pillow
                frame_size=(original_width, original_height)
            )
        
        return QuadResult(
            detected=False,
            frame_size=(original_width, original_height)
        )
    
    def _find_content_bbox(self, edges_img: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """Find bounding box of content in edge image."""
        # Convert to pixels
        pixels = list(edges_img.getdata())
        width, height = edges_img.size
        
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        edge_count = 0
        
        for y in range(height):
            for x in range(width):
                if pixels[y * width + x] > 128:
                    edge_count += 1
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        
        # Require minimum edge pixels
        if edge_count < 100:
            return None
        
        # Add margin
        margin = 10
        min_x = max(0, min_x - margin)
        min_y = max(0, min_y - margin)
        max_x = min(width - 1, max_x + margin)
        max_y = min(height - 1, max_y + margin)
        
        # Check for reasonable size
        box_width = max_x - min_x
        box_height = max_y - min_y
        
        if box_width < width * 0.2 or box_height < height * 0.2:
            return None
        
        return (min_x, min_y, max_x, max_y)
    
    def _order_points(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Order points clockwise starting from top-left."""
        # Convert to numpy for easier manipulation
        pts = np.array(points, dtype=np.float32)
        
        # Sort by sum (x + y) to find TL and BR
        s = pts.sum(axis=1)
        tl_idx = np.argmin(s)
        br_idx = np.argmax(s)
        
        # Sort by difference (y - x) to find TR and BL
        d = np.diff(pts, axis=1)
        tr_idx = np.argmin(d)
        bl_idx = np.argmax(d)
        
        ordered = [
            tuple(pts[tl_idx].astype(int)),
            tuple(pts[tr_idx].astype(int)),
            tuple(pts[br_idx].astype(int)),
            tuple(pts[bl_idx].astype(int)),
        ]
        
        return ordered
    
    def get_full_frame_quad(self, width: int, height: int, margin: int = 20) -> List[Tuple[int, int]]:
        """Return quad points for full frame (fallback when detection fails)."""
        return [
            (margin, margin),
            (width - margin, margin),
            (width - margin, height - margin),
            (margin, height - margin),
        ]
    
    def estimate_brightness(self, image_path: str) -> float:
        """Estimate average brightness of image (0-255)."""
        try:
            img = Image.open(image_path)
            gray = img.convert('L')
            # Sample center region
            width, height = gray.size
            cx, cy = width // 2, height // 2
            sample_size = min(200, width // 2, height // 2)
            crop = gray.crop((
                cx - sample_size, cy - sample_size,
                cx + sample_size, cy + sample_size
            ))
            # Calculate mean brightness
            pixels = list(crop.getdata())
            return sum(pixels) / len(pixels) if pixels else 128
        except:
            return 128  # Default to mid-brightness
    
    def is_low_light(self, image_path: str, threshold: float = 50) -> bool:
        """Check if image appears to be in low light conditions."""
        return self.estimate_brightness(image_path) < threshold
