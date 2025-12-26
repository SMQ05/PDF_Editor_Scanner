"""
EXIF Sanitization for PDF Scanner App.
Strips metadata from images for privacy protection.
"""
import os
from kivy.logger import Logger
from PIL import Image


def sanitize_image(image_path: str, output_path: str = None) -> str:
    """
    Remove EXIF metadata from image for privacy.
    
    Args:
        image_path: Path to source image
        output_path: Optional output path (defaults to temp file)
        
    Returns:
        Path to sanitized image
    """
    try:
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_sanitized.jpg"
        
        # Open image
        img = Image.open(image_path)
        
        # Get image data without EXIF
        data = list(img.getdata())
        
        # Create new image without metadata
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        
        # Convert to RGB if necessary (for JPEG)
        if clean_img.mode == 'RGBA':
            clean_img = clean_img.convert('RGB')
        elif clean_img.mode not in ('RGB', 'L'):
            clean_img = clean_img.convert('RGB')
        
        # Save without EXIF
        clean_img.save(output_path, 'JPEG', quality=95)
        
        Logger.info(f"EXIF: Sanitized image saved to {output_path}")
        return output_path
        
    except Exception as e:
        Logger.error(f"EXIF: Sanitization failed: {e}")
        # Return original path on failure
        return image_path


def strip_exif_in_place(image_path: str) -> bool:
    """
    Strip EXIF metadata from image in place.
    
    Args:
        image_path: Path to image to modify
        
    Returns:
        True if successful, False otherwise
    """
    try:
        img = Image.open(image_path)
        
        # Check if EXIF exists
        exif = img.getexif()
        if not exif:
            Logger.info("EXIF: No metadata found")
            return True
        
        # Get image data
        data = list(img.getdata())
        
        # Create clean image
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        
        # Convert mode if needed
        if clean_img.mode == 'RGBA':
            clean_img = clean_img.convert('RGB')
        
        # Save back to same path
        clean_img.save(image_path, 'JPEG', quality=95)
        
        Logger.info(f"EXIF: Stripped metadata from {image_path}")
        return True
        
    except Exception as e:
        Logger.error(f"EXIF: In-place strip failed: {e}")
        return False


def check_has_gps(image_path: str) -> bool:
    """
    Check if image contains GPS metadata.
    
    Args:
        image_path: Path to image
        
    Returns:
        True if GPS data found, False otherwise
    """
    try:
        img = Image.open(image_path)
        exif = img.getexif()
        
        if not exif:
            return False
        
        # GPS tag IDs
        GPS_TAG_ID = 34853  # GPSInfo tag
        
        # Check for GPS tag
        if GPS_TAG_ID in exif:
            return True
        
        # Also check IFD
        try:
            from PIL.ExifTags import IFD
            gps_ifd = exif.get_ifd(IFD.GPSInfo)
            if gps_ifd:
                return True
        except:
            pass
        
        return False
        
    except Exception as e:
        Logger.error(f"EXIF: GPS check failed: {e}")
        return False


def get_image_metadata_summary(image_path: str) -> dict:
    """
    Get summary of image metadata (for debugging).
    
    Args:
        image_path: Path to image
        
    Returns:
        Dictionary with metadata summary
    """
    try:
        img = Image.open(image_path)
        exif = img.getexif()
        
        summary = {
            'has_exif': bool(exif),
            'size': img.size,
            'mode': img.mode,
            'format': img.format,
        }
        
        if exif:
            # Common interesting tags
            from PIL.ExifTags import TAGS
            
            tag_names = []
            for tag_id in exif.keys():
                tag_name = TAGS.get(tag_id, str(tag_id))
                tag_names.append(tag_name)
            
            summary['exif_tags'] = tag_names[:20]  # Limit
            summary['has_gps'] = check_has_gps(image_path)
        
        return summary
        
    except Exception as e:
        Logger.error(f"EXIF: Metadata summary failed: {e}")
        return {'error': str(e)}
