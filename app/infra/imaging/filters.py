"""
Image Filters for PDF Scanner App.
Provides B/W, Grayscale, and Enhanced filters for scanned documents.

Supports:
- OpenCV (preferred for adaptive threshold)
- Pillow fallback
"""
import os
from typing import Optional
from kivy.logger import Logger

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from PIL import Image, ImageEnhance, ImageOps, ImageFilter

from app.domain.models import FilterType


class ImageFilters:
    """Applies various filters to scanned document images."""
    
    def __init__(self):
        self.use_opencv = OPENCV_AVAILABLE
    
    def apply_filter(self, image_path: str, filter_type: FilterType,
                     output_path: str = None) -> str:
        """
        Apply specified filter to image.
        
        Args:
            image_path: Path to source image
            filter_type: Type of filter to apply
            output_path: Optional output path
            
        Returns:
            Path to filtered image
        """
        try:
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_{filter_type.value}.jpg"
            
            if filter_type == FilterType.ORIGINAL:
                return image_path
            elif filter_type == FilterType.GRAYSCALE:
                return self._apply_grayscale(image_path, output_path)
            elif filter_type == FilterType.BLACK_WHITE:
                return self._apply_black_white(image_path, output_path)
            elif filter_type == FilterType.ENHANCED:
                return self._apply_enhanced(image_path, output_path)
            else:
                return image_path
        except Exception as e:
            Logger.error(f"Filters: Failed to apply {filter_type.value}: {e}")
            return image_path
    
    def _apply_grayscale(self, image_path: str, output_path: str) -> str:
        """Convert image to grayscale."""
        img = Image.open(image_path)
        gray = img.convert('L')
        gray.save(output_path, 'JPEG', quality=90)
        Logger.info(f"Filters: Applied grayscale to {output_path}")
        return output_path
    
    def _apply_black_white(self, image_path: str, output_path: str) -> str:
        """Apply adaptive threshold for clean B/W document look."""
        if self.use_opencv:
            return self._apply_bw_opencv(image_path, output_path)
        else:
            return self._apply_bw_pillow(image_path, output_path)
    
    def _apply_bw_opencv(self, image_path: str, output_path: str) -> str:
        """Apply adaptive threshold using OpenCV."""
        img = cv2.imread(image_path)
        if img is None:
            return self._apply_bw_pillow(image_path, output_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive threshold for clean document look
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21,
            C=10
        )
        
        cv2.imwrite(output_path, binary, [cv2.IMWRITE_JPEG_QUALITY, 90])
        Logger.info(f"Filters: Applied B/W (OpenCV) to {output_path}")
        return output_path
    
    def _apply_bw_pillow(self, image_path: str, output_path: str) -> str:
        """Apply threshold using Pillow (simpler, less adaptive)."""
        img = Image.open(image_path)
        gray = img.convert('L')
        
        # Apply slight blur
        blurred = gray.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Calculate adaptive threshold (simplified)
        # Use local contrast enhancement first
        enhancer = ImageEnhance.Contrast(blurred)
        enhanced = enhancer.enhance(2.0)
        
        # Then threshold
        threshold = 140
        binary = enhanced.point(lambda x: 255 if x > threshold else 0, '1')
        
        # Convert back to grayscale for JPEG save
        binary = binary.convert('L')
        binary.save(output_path, 'JPEG', quality=90)
        
        Logger.info(f"Filters: Applied B/W (Pillow) to {output_path}")
        return output_path
    
    def _apply_enhanced(self, image_path: str, output_path: str) -> str:
        """Apply contrast enhancement (CLAHE or Pillow enhance)."""
        if self.use_opencv:
            return self._apply_enhanced_opencv(image_path, output_path)
        else:
            return self._apply_enhanced_pillow(image_path, output_path)
    
    def _apply_enhanced_opencv(self, image_path: str, output_path: str) -> str:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        img = cv2.imread(image_path)
        if img is None:
            return self._apply_enhanced_pillow(image_path, output_path)
        
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge channels and convert back
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # Slight sharpening
        kernel = np.array([[-0.5, -0.5, -0.5],
                           [-0.5,  5,   -0.5],
                           [-0.5, -0.5, -0.5]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Blend original and sharpened
        result = cv2.addWeighted(enhanced, 0.7, sharpened, 0.3, 0)
        
        cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 90])
        Logger.info(f"Filters: Applied enhanced (CLAHE) to {output_path}")
        return output_path
    
    def _apply_enhanced_pillow(self, image_path: str, output_path: str) -> str:
        """Apply enhancement using Pillow."""
        img = Image.open(image_path)
        
        # Auto-contrast
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = ImageOps.autocontrast(img, cutoff=1)
        
        # Increase contrast
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(1.3)
        
        # Increase sharpness
        sharpness = ImageEnhance.Sharpness(img)
        img = sharpness.enhance(1.5)
        
        # Slight brightness adjustment
        brightness = ImageEnhance.Brightness(img)
        img = brightness.enhance(1.05)
        
        img.save(output_path, 'JPEG', quality=90)
        Logger.info(f"Filters: Applied enhanced (Pillow) to {output_path}")
        return output_path
    
    def get_preview(self, image_path: str, filter_type: FilterType,
                    max_size: int = 300) -> Optional[Image.Image]:
        """
        Generate a small preview of the filter effect.
        Used for filter selection UI.
        
        Args:
            image_path: Path to source image
            filter_type: Filter to preview
            max_size: Maximum dimension for preview
            
        Returns:
            PIL Image object or None on failure
        """
        try:
            img = Image.open(image_path)
            
            # Resize for preview
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            if filter_type == FilterType.ORIGINAL:
                return img.convert('RGB')
            elif filter_type == FilterType.GRAYSCALE:
                return img.convert('L').convert('RGB')
            elif filter_type == FilterType.BLACK_WHITE:
                gray = img.convert('L')
                enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
                binary = enhanced.point(lambda x: 255 if x > 140 else 0)
                return binary.convert('RGB')
            elif filter_type == FilterType.ENHANCED:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img = ImageOps.autocontrast(img, cutoff=1)
                img = ImageEnhance.Contrast(img).enhance(1.3)
                return img
            
            return img.convert('RGB')
        except Exception as e:
            Logger.error(f"Filters: Preview failed: {e}")
            return None
