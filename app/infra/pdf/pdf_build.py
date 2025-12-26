"""
PDF Builder for PDF Scanner App.
Converts images to PDF using available libraries.
"""
import os
from typing import List, Optional
from kivy.logger import Logger

from PIL import Image


class PDFBuilder:
    """Builds PDF files from scanned images."""
    
    # PDF metadata for privacy
    NEUTRAL_CREATOR = "PDF Scanner"
    NEUTRAL_AUTHOR = ""
    
    def __init__(self):
        pass
    
    def images_to_pdf(self, image_paths: List[str], output_path: str,
                      title: str = None) -> bool:
        """
        Convert a list of images to a PDF file.
        
        Args:
            image_paths: List of paths to image files
            output_path: Output PDF file path
            title: Optional title for PDF metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not image_paths:
            Logger.error("PDFBuilder: No images provided")
            return False
        
        # Try img2pdf first (better quality, maintains resolution)
        try:
            return self._build_with_img2pdf(image_paths, output_path, title)
        except ImportError:
            Logger.info("PDFBuilder: img2pdf not available, using Pillow")
        except Exception as e:
            Logger.warning(f"PDFBuilder: img2pdf failed: {e}, trying Pillow")
        
        # Fallback to Pillow
        try:
            return self._build_with_pillow(image_paths, output_path, title)
        except Exception as e:
            Logger.error(f"PDFBuilder: Pillow build failed: {e}")
            return False
    
    def _build_with_img2pdf(self, image_paths: List[str], output_path: str,
                            title: str = None) -> bool:
        """Build PDF using img2pdf library."""
        import img2pdf
        
        # Read images as bytes
        image_bytes_list = []
        for path in image_paths:
            if not os.path.exists(path):
                Logger.warning(f"PDFBuilder: Image not found: {path}")
                continue
            
            with open(path, 'rb') as f:
                image_bytes_list.append(f.read())
        
        if not image_bytes_list:
            return False
        
        # Convert to PDF
        pdf_bytes = img2pdf.convert(image_bytes_list)
        
        # Write output
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Update metadata to neutral values
        self._sanitize_pdf_metadata(output_path, title)
        
        Logger.info(f"PDFBuilder: Created PDF with img2pdf: {output_path}")
        return True
    
    def _build_with_pillow(self, image_paths: List[str], output_path: str,
                           title: str = None) -> bool:
        """Build PDF using Pillow's save method."""
        images = []
        first_image = None
        
        for path in image_paths:
            if not os.path.exists(path):
                Logger.warning(f"PDFBuilder: Image not found: {path}")
                continue
            
            try:
                img = Image.open(path)
                
                # Convert to RGB if necessary (PDF doesn't support RGBA)
                if img.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha as mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if first_image is None:
                    first_image = img
                else:
                    images.append(img)
                    
            except Exception as e:
                Logger.warning(f"PDFBuilder: Failed to load image {path}: {e}")
        
        if first_image is None:
            return False
        
        # Save as PDF
        if images:
            first_image.save(
                output_path, 'PDF',
                save_all=True,
                append_images=images,
                resolution=150.0
            )
        else:
            first_image.save(output_path, 'PDF', resolution=150.0)
        
        # Sanitize metadata
        self._sanitize_pdf_metadata(output_path, title)
        
        Logger.info(f"PDFBuilder: Created PDF with Pillow: {output_path}")
        return True
    
    def _sanitize_pdf_metadata(self, pdf_path: str, title: str = None):
        """
        Remove/neutralize PDF metadata for privacy.
        Uses pypdf to update metadata.
        """
        try:
            from pypdf import PdfReader, PdfWriter
            
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Set neutral metadata
            writer.add_metadata({
                '/Creator': self.NEUTRAL_CREATOR,
                '/Producer': self.NEUTRAL_CREATOR,
                '/Author': self.NEUTRAL_AUTHOR,
                '/Title': title or '',
                '/Subject': '',
                '/Keywords': '',
            })
            
            # Write back
            with open(pdf_path, 'wb') as f:
                writer.write(f)
            
            Logger.info("PDFBuilder: Sanitized PDF metadata")
            
        except ImportError:
            Logger.warning("PDFBuilder: pypdf not available for metadata sanitization")
        except Exception as e:
            Logger.warning(f"PDFBuilder: Metadata sanitization failed: {e}")
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            Logger.error(f"PDFBuilder: Failed to get page count: {e}")
            return 0
    
    def extract_first_page_image(self, pdf_path: str, output_path: str,
                                  max_size: int = 300) -> Optional[str]:
        """
        Extract first page as image for thumbnail.
        
        Note: This is a simplified implementation. For full rendering,
        you'd need pdf2image or similar, which requires poppler.
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(pdf_path)
            if not reader.pages:
                return None
            
            first_page = reader.pages[0]
            
            # Try to extract embedded images
            images = []
            if '/XObject' in first_page.get('/Resources', {}):
                x_object = first_page['/Resources']['/XObject'].get_object()
                for obj in x_object:
                    if x_object[obj]['/Subtype'] == '/Image':
                        images.append(obj)
            
            if images:
                # Extract first image
                x_object = first_page['/Resources']['/XObject'].get_object()
                img_obj = x_object[images[0]]
                
                # For now, return None - full image extraction is complex
                # Would need to handle various image encodings
                pass
            
            return None
            
        except Exception as e:
            Logger.error(f"PDFBuilder: Image extraction failed: {e}")
            return None
