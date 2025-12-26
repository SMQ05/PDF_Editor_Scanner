"""
PDF Tools for PDF Scanner App.
Merge, split, and analyze PDF files.
"""
import os
from typing import List, Tuple, Optional, Callable
from kivy.logger import Logger


class PDFTools:
    """PDF manipulation utilities - merge, split, encryption detection."""
    
    def __init__(self):
        pass
    
    def is_encrypted(self, pdf_path: str) -> bool:
        """
        Check if a PDF file is encrypted/password-protected.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if encrypted, False otherwise
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(pdf_path)
            return reader.is_encrypted
            
        except Exception as e:
            Logger.error(f"PDFTools: Encryption check failed: {e}")
            # Return True on error to be safe (don't process unknown files)
            return True
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages, or 0 on error
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(pdf_path)
            if reader.is_encrypted:
                return 0
            return len(reader.pages)
            
        except Exception as e:
            Logger.error(f"PDFTools: Page count failed: {e}")
            return 0
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str,
                   progress_callback: Callable[[int, int], None] = None) -> bool:
        """
        Merge multiple PDFs into one.
        
        Args:
            pdf_paths: List of PDF file paths to merge
            output_path: Output merged PDF path
            progress_callback: Optional callback(current, total)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from pypdf import PdfWriter, PdfReader
            
            writer = PdfWriter()
            total = len(pdf_paths)
            
            for i, path in enumerate(pdf_paths):
                if not os.path.exists(path):
                    Logger.warning(f"PDFTools: File not found: {path}")
                    continue
                
                if progress_callback:
                    progress_callback(i + 1, total)
                
                try:
                    reader = PdfReader(path)
                    
                    if reader.is_encrypted:
                        Logger.warning(f"PDFTools: Skipping encrypted PDF: {path}")
                        continue
                    
                    for page in reader.pages:
                        writer.add_page(page)
                        
                except Exception as e:
                    Logger.error(f"PDFTools: Error reading {path}: {e}")
                    continue
            
            if len(writer.pages) == 0:
                Logger.error("PDFTools: No pages to merge")
                return False
            
            # Set neutral metadata
            writer.add_metadata({
                '/Creator': 'PDF Scanner',
                '/Producer': 'PDF Scanner',
                '/Author': '',
            })
            
            # Write output
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            Logger.info(f"PDFTools: Merged {total} PDFs into {output_path}")
            return True
            
        except Exception as e:
            Logger.error(f"PDFTools: Merge failed: {e}")
            return False
    
    def split_pdf(self, pdf_path: str, page_ranges: List[Tuple[int, int]],
                  output_dir: str, output_prefix: str) -> List[str]:
        """
        Split a PDF into multiple files by page ranges.
        
        Args:
            pdf_path: Path to source PDF
            page_ranges: List of (start, end) tuples (1-indexed, inclusive)
            output_dir: Directory for output files
            output_prefix: Prefix for output filenames
            
        Returns:
            List of created file paths, empty list on failure
        """
        try:
            from pypdf import PdfReader, PdfWriter
            
            reader = PdfReader(pdf_path)
            
            if reader.is_encrypted:
                Logger.error("PDFTools: Cannot split encrypted PDF")
                return []
            
            total_pages = len(reader.pages)
            output_paths = []
            
            os.makedirs(output_dir, exist_ok=True)
            
            for i, (start, end) in enumerate(page_ranges):
                # Validate range (convert to 0-indexed)
                start_idx = max(0, start - 1)
                end_idx = min(total_pages, end)
                
                if start_idx >= end_idx:
                    Logger.warning(f"PDFTools: Invalid range {start}-{end}")
                    continue
                
                writer = PdfWriter()
                
                for page_idx in range(start_idx, end_idx):
                    writer.add_page(reader.pages[page_idx])
                
                # Set neutral metadata
                writer.add_metadata({
                    '/Creator': 'PDF Scanner',
                    '/Producer': 'PDF Scanner',
                })
                
                # Generate output filename
                output_filename = f"{output_prefix}_part{i + 1}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'wb') as f:
                    writer.write(f)
                
                output_paths.append(output_path)
                Logger.info(f"PDFTools: Created split PDF: {output_path}")
            
            return output_paths
            
        except Exception as e:
            Logger.error(f"PDFTools: Split failed: {e}")
            return []
    
    def extract_pages(self, pdf_path: str, page_numbers: List[int],
                      output_path: str) -> bool:
        """
        Extract specific pages from a PDF.
        
        Args:
            pdf_path: Source PDF path
            page_numbers: List of page numbers to extract (1-indexed)
            output_path: Output PDF path
            
        Returns:
            True if successful
        """
        try:
            from pypdf import PdfReader, PdfWriter
            
            reader = PdfReader(pdf_path)
            
            if reader.is_encrypted:
                Logger.error("PDFTools: Cannot extract from encrypted PDF")
                return False
            
            total_pages = len(reader.pages)
            writer = PdfWriter()
            
            for page_num in page_numbers:
                page_idx = page_num - 1  # Convert to 0-indexed
                if 0 <= page_idx < total_pages:
                    writer.add_page(reader.pages[page_idx])
                else:
                    Logger.warning(f"PDFTools: Page {page_num} out of range")
            
            if len(writer.pages) == 0:
                Logger.error("PDFTools: No valid pages to extract")
                return False
            
            writer.add_metadata({
                '/Creator': 'PDF Scanner',
                '/Producer': 'PDF Scanner',
            })
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            Logger.info(f"PDFTools: Extracted {len(page_numbers)} pages to {output_path}")
            return True
            
        except Exception as e:
            Logger.error(f"PDFTools: Extract failed: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get information about a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF info
        """
        info = {
            'path': pdf_path,
            'exists': os.path.exists(pdf_path),
            'file_size': 0,
            'page_count': 0,
            'is_encrypted': False,
            'error': None,
        }
        
        if not info['exists']:
            info['error'] = 'File not found'
            return info
        
        info['file_size'] = os.path.getsize(pdf_path)
        
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(pdf_path)
            info['is_encrypted'] = reader.is_encrypted
            
            if not reader.is_encrypted:
                info['page_count'] = len(reader.pages)
                
                # Get metadata if available
                if reader.metadata:
                    info['title'] = reader.metadata.get('/Title', '')
                    info['author'] = reader.metadata.get('/Author', '')
                    info['creator'] = reader.metadata.get('/Creator', '')
                    
        except Exception as e:
            info['error'] = str(e)
        
        return info
