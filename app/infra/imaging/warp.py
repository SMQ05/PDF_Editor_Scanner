"""
Perspective Warp for PDF Scanner App.
Transforms document quad to rectangular image.

Supports:
- OpenCV (preferred, if available)
- Pillow fallback
"""
from typing import List, Tuple, Optional
import os
from kivy.logger import Logger

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from PIL import Image


class PerspectiveWarper:
    """Transforms perspective-distorted documents to rectangular images."""
    
    def __init__(self):
        self.use_opencv = OPENCV_AVAILABLE
    
    def warp(self, image_path: str, quad_points: List[Tuple[int, int]], 
             output_path: str = None) -> str:
        """
        Warp image using quad points to produce rectangular output.
        
        Args:
            image_path: Path to source image
            quad_points: 4 corners in order [TL, TR, BR, BL]
            output_path: Optional output path, defaults to temp file
            
        Returns:
            Path to warped image
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_warped.jpg"
            
            if self.use_opencv:
                return self._warp_opencv(image_path, quad_points, output_path)
            else:
                return self._warp_pillow(image_path, quad_points, output_path)
        except Exception as e:
            Logger.error(f"Warp: Failed to warp image: {e}")
            # Return original on failure
            return image_path
    
    def _warp_opencv(self, image_path: str, quad_points: List[Tuple[int, int]], 
                     output_path: str) -> str:
        """Warp using OpenCV getPerspectiveTransform."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Calculate output dimensions based on quad
        width, height = self._calculate_output_size(quad_points)
        
        # Source points (quad)
        src_pts = np.float32(quad_points)
        
        # Destination points (rectangle)
        dst_pts = np.float32([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ])
        
        # Get perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Apply warp
        warped = cv2.warpPerspective(img, matrix, (width, height))
        
        # Save result
        cv2.imwrite(output_path, warped, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        Logger.info(f"Warp: Created warped image {output_path}")
        return output_path
    
    def _warp_pillow(self, image_path: str, quad_points: List[Tuple[int, int]], 
                     output_path: str) -> str:
        """Warp using Pillow transform (less accurate but works)."""
        img = Image.open(image_path)
        
        # Calculate output dimensions
        width, height = self._calculate_output_size(quad_points)
        
        # Pillow's transform needs coefficients for perspective transform
        # We'll use the QUAD transform which maps 4 corners
        # The quad parameter is: (x0, y0, x1, y1, x2, y2, x3, y3)
        # representing the corners of the source quadrilateral
        
        # Flatten quad points for Pillow
        # Order: top-left, top-right, bottom-right, bottom-left
        quad_flat = []
        for pt in quad_points:
            quad_flat.extend(pt)
        
        # Transform image
        warped = img.transform(
            (width, height),
            Image.Transform.QUAD,
            quad_flat,
            Image.Resampling.BICUBIC
        )
        
        # Save as JPEG
        if warped.mode == 'RGBA':
            warped = warped.convert('RGB')
        warped.save(output_path, 'JPEG', quality=95)
        
        Logger.info(f"Warp: Created warped image (Pillow) {output_path}")
        return output_path
    
    def _calculate_output_size(self, quad_points: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Calculate output image size based on quad dimensions."""
        # Points: TL, TR, BR, BL
        tl, tr, br, bl = quad_points
        
        # Calculate widths (top and bottom edges)
        width_top = self._distance(tl, tr)
        width_bottom = self._distance(bl, br)
        width = int(max(width_top, width_bottom))
        
        # Calculate heights (left and right edges)
        height_left = self._distance(tl, bl)
        height_right = self._distance(tr, br)
        height = int(max(height_left, height_right))
        
        # Ensure minimum size
        width = max(width, 100)
        height = max(height, 100)
        
        return width, height
    
    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points."""
        return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
    
    def rotate_image(self, image_path: str, degrees: int, output_path: str = None) -> str:
        """
        Rotate image by specified degrees (90, 180, 270).
        
        Args:
            image_path: Path to source image
            degrees: Rotation in degrees (positive = counterclockwise)
            output_path: Optional output path
            
        Returns:
            Path to rotated image
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_rotated.jpg"
            
            # Normalize degrees
            degrees = degrees % 360
            if degrees == 0:
                return image_path
            
            img = Image.open(image_path)
            
            # Pillow rotate is counterclockwise
            rotated = img.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)
            
            if rotated.mode == 'RGBA':
                rotated = rotated.convert('RGB')
            rotated.save(output_path, 'JPEG', quality=95)
            
            Logger.info(f"Warp: Rotated image by {degrees}°")
            return output_path
        except Exception as e:
            Logger.error(f"Warp: Rotation failed: {e}")
            return image_path
    
    def deskew(self, image_path: str, output_path: str = None) -> str:
        """
        Attempt to auto-correct slight rotation (deskew).
        
        Args:
            image_path: Path to source image
            output_path: Optional output path
            
        Returns:
            Path to deskewed image
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_deskewed.jpg"
            
            if self.use_opencv:
                return self._deskew_opencv(image_path, output_path)
            else:
                # Pillow fallback: no deskew, return original
                Logger.info("Warp: Deskew not available without OpenCV")
                return image_path
        except Exception as e:
            Logger.error(f"Warp: Deskew failed: {e}")
            return image_path
    
    def _deskew_opencv(self, image_path: str, output_path: str) -> str:
        """Deskew using OpenCV Hough transform."""
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None or len(lines) == 0:
            return image_path
        
        # Calculate dominant angle
        angles = []
        for line in lines[:20]:  # Limit to first 20 lines
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if -45 < angle < 45:  # Only consider small angles
                angles.append(angle)
        
        if not angles:
            return image_path
        
        # Use median angle for robustness
        median_angle = np.median(angles)
        
        # Only deskew if angle is significant but not too large
        if abs(median_angle) < 0.5 or abs(median_angle) > 15:
            return image_path
        
        # Rotate to correct skew
        height, width = img.shape[:2]
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(img, rotation_matrix, (width, height),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)
        
        cv2.imwrite(output_path, rotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
        Logger.info(f"Warp: Deskewed by {median_angle:.2f}°")
        return output_path
