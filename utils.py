"""
Utility functions for the PDF Intelligence System
"""

import logging
import sys
from pathlib import Path
from typing import Union, List

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def is_pdf_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a PDF"""
    path = Path(file_path)
    return path.is_file() and path.suffix.lower() == '.pdf'

def validate_input_directory(input_dir: str) -> bool:
    """Validate input directory exists and contains PDFs"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        return False
    
    if not input_path.is_dir():
        return False
    
    # Check for at least one PDF file
    pdf_files = [f for f in input_path.iterdir() if is_pdf_file(f)]
    return len(pdf_files) > 0

def get_pdf_files(directory: str) -> List[Path]:
    """Get list of PDF files in directory"""
    dir_path = Path(directory)
    return [f for f in dir_path.iterdir() if is_pdf_file(f)]

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters"""
    import re
    
    # Remove or replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)
    
    # Limit length
    if len(safe_name) > 200:
        name_part = safe_name[:190]
        extension = safe_name[-10:] if '.' in safe_name[-10:] else ''
        safe_name = name_part + extension
    
    return safe_name

def create_output_directory(output_dir: str) -> None:
    """Create output directory if it doesn't exist"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_json_output(data: dict, schema_type: str) -> bool:
    """Validate JSON output against expected schema"""
    if schema_type == "round1a":
        required_fields = ["title", "outline"]
        if not all(field in data for field in required_fields):
            return False
        
        if not isinstance(data["outline"], list):
            return False
        
        for item in data["outline"]:
            if not all(field in item for field in ["level", "text", "page"]):
                return False
    
    elif schema_type == "round1b":
        required_fields = ["metadata", "extracted_sections", "subsection_analysis"]
        if not all(field in data for field in required_fields):
            return False
        
        metadata_fields = ["input_documents", "persona", "job_to_be_done", "processing_timestamp"]
        if not all(field in data["metadata"] for field in metadata_fields):
            return False
    
    return True

class ProgressTracker:
    """Simple progress tracking utility"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.logger = logging.getLogger(__name__)
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
        percentage = (self.current / self.total) * 100
        self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def finish(self):
        """Mark as completed"""
        self.logger.info(f"{self.description}: Completed ({self.total}/{self.total})")

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def clean_text_for_json(text: str) -> str:
    """Clean text for JSON serialization"""
    if not text:
        return ""
    
    # Replace problematic characters
    text = text.replace('\x00', '')  # Remove null bytes
    text = text.replace('\r\n', '\n')  # Normalize line endings
    text = text.replace('\r', '\n')
    
    return text.strip()
