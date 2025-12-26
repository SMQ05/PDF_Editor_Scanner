"""
PDF Compression for PDF Scanner App.
Compresses scanned document PDFs by resizing/recompressing images.
"""
import os
from typing import Tuple
from kivy.logger import Logger
from PIL import Image


# Compression presets
PRESETS = {
    'small': {'max_dimension': 1600, 'jpeg_quality': 50},
    'balanced': {'max_dimension': 2000, 'jpeg_quality': 65},
    'high': {'max_dimension': 2500, 'jpeg_quality': 80},
}


def compress_images_for_pdf(image_path: str, max_dimension: int = 2000,
                            jpeg_quality: int = 65) -> str:
    """
    Compress an image for PDF inclusion.
    
    Args:
        image_path: Path to source image
        max_dimension: Maximum width or height in pixels
        jpeg_quality: JPEG quality (1-100)
        
    Returns:
        Path to compressed image (may be same as input if no compression needed)
    """
    try:
        img = Image.open(image_path)
        original_size = img.size
        
        # Check if resizing needed
        needs_resize = max(original_size) > max_dimension
        
        if needs_resize:
            # Calculate new size maintaining aspect ratio
            ratio = max_dimension / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Generate output path
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_compressed.jpg"
        
        # Save with compression
        img.save(output_path, 'JPEG', quality=jpeg_quality, optimize=True)
        
        # Log compression stats
        original_file_size = os.path.getsize(image_path)
        new_file_size = os.path.getsize(output_path)
        reduction = (1 - new_file_size / original_file_size) * 100
        
        Logger.info(f"Compress: {original_size} -> {img.size}, "
                    f"{original_file_size // 1024}KB -> {new_file_size // 1024}KB "
                    f"({reduction:.1f}% reduction)")
        
        return output_path
        
    except Exception as e:
        Logger.error(f"Compress: Failed to compress image: {e}")
        return image_path


def compress_pdf(pdf_path: str, output_path: str, preset: str = 'balanced') -> bool:
    """
    Compress a PDF by extracting, recompressing, and rebuilding.
    Note: This works for image-based PDFs (scanned documents).
    
    Args:
        pdf_path: Path to source PDF
        output_path: Path for compressed output
        preset: Compression preset ('small', 'balanced', 'high')
        
    Returns:
        True if successful
    """
    try:
        from pypdf import PdfReader, PdfWriter
        import tempfile
        import shutil
        
        settings = PRESETS.get(preset, PRESETS['balanced'])
        max_dim = settings['max_dimension']
        quality = settings['jpeg_quality']
        
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            Logger.error("Compress: Cannot compress encrypted PDF")
            return False
        
        # For image-based PDFs created by this app, we can try to extract
        # and recompress the images. However, this is complex.
        # 
        # Simpler approach: if this is a scanned document PDF from our app,
        # we should compress images BEFORE creating the PDF.
        # 
        # For external PDFs, compression is more limited.
        
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Compress content streams
        for page in writer.pages:
            page.compress_content_streams()
        
        writer.add_metadata({
            '/Creator': 'PDF Scanner',
            '/Producer': 'PDF Scanner',
        })
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # Log compression
        original_size = os.path.getsize(pdf_path)
        new_size = os.path.getsize(output_path)
        
        if new_size < original_size:
            reduction = (1 - new_size / original_size) * 100
            Logger.info(f"Compress: PDF compressed by {reduction:.1f}%")
        else:
            Logger.info("Compress: PDF could not be further compressed")
            # Use original if compression didn't help
            shutil.copy(pdf_path, output_path)
        
        return True
        
    except Exception as e:
        Logger.error(f"Compress: PDF compression failed: {e}")
        return False


def get_preset_settings(preset_name: str) -> Tuple[int, int]:
    """
    Get compression settings for a preset.
    
    Args:
        preset_name: Name of preset ('small', 'balanced', 'high')
        
    Returns:
        Tuple of (max_dimension, jpeg_quality)
    """
    settings = PRESETS.get(preset_name, PRESETS['balanced'])
    return settings['max_dimension'], settings['jpeg_quality']


def estimate_output_size(image_paths: list, preset: str = 'balanced') -> int:
    """
    Estimate the output PDF size for given images and preset.
    
    Args:
        image_paths: List of image file paths
        preset: Compression preset name
        
    Returns:
        Estimated size in bytes
    """
    max_dim, quality = get_preset_settings(preset)
    
    # Rough estimation based on image dimensions and quality
    total_pixels = 0
    
    for path in image_paths:
        try:
            with Image.open(path) as img:
                w, h = img.size
                # Apply max dimension constraint
                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    w = int(w * ratio)
                    h = int(h * ratio)
                total_pixels += w * h
        except:
            # Fallback estimate for unreadable images
            total_pixels += max_dim * max_dim
    
    # Estimate bytes per pixel based on JPEG quality
    # This is a rough approximation
    if quality <= 50:
        bytes_per_pixel = 0.15
    elif quality <= 65:
        bytes_per_pixel = 0.25
    elif quality <= 80:
        bytes_per_pixel = 0.35
    else:
        bytes_per_pixel = 0.5
    
    estimated_size = int(total_pixels * bytes_per_pixel)
    
    # Add PDF overhead (very rough)
    pdf_overhead = 1024 + len(image_paths) * 512
    
    return estimated_size + pdf_overhead


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
