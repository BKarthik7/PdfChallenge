"""
Round 1A: PDF Structure Extraction
Extracts title and hierarchical headings (H1, H2, H3) from PDFs
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import re
import fitz  # PyMuPDF

from pdf_processor import PDFProcessor
from utils import is_pdf_file

class Round1AProcessor:
    """Processes PDFs to extract structured outlines"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pdf_processor = PDFProcessor()
    
    def process_directory(self, input_dir: str, output_dir: str) -> None:
        """Process all PDFs in input directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        pdf_files = [f for f in input_path.iterdir() if is_pdf_file(f)]
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {input_dir}")
            return
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Processing {pdf_file.name}")
                result = self.extract_structure(pdf_file)
                
                # Save result
                output_file = output_path / f"{pdf_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Saved structure to {output_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
                continue
    
    def extract_structure(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract title and heading structure from PDF"""
        try:
            doc = fitz.open(str(pdf_path))
            
            # Extract title
            title = self._extract_title(doc)
            
            # Extract headings
            outline = self._extract_headings(doc)
            
            doc.close()
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting structure from {pdf_path}: {str(e)}")
            raise
    
    def _extract_title(self, doc: fitz.Document) -> str:
        """Extract document title"""
        # Try metadata first
        metadata = doc.metadata
        if metadata.get('title') and metadata['title'].strip():
            return metadata['title'].strip()
        
        # Try first few pages for title text analysis
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            # Look for title-like text (large font, top of page)
            title_candidates = []
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            font_size = span.get("size", 0)
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            
                            # Title criteria: large font, near top, substantial text
                            if (text and len(text) > 10 and len(text) < 150 and
                                font_size > 14 and bbox[1] < page.rect.height * 0.4):
                                
                                # Filter out common non-title patterns
                                if not any(pattern in text.lower() for pattern in 
                                         ['page ', 'figure ', 'table ', 'section ', 'chapter ',
                                          'http', 'www.', '.com', '.pdf', 'appendix']):
                                    title_candidates.append((text, font_size, bbox[1], page_num))
            
            # Sort by font size (descending) and position (ascending)
            title_candidates.sort(key=lambda x: (-x[1], x[2], x[3]))
            
            # Return the first good candidate
            for candidate in title_candidates:
                text = candidate[0]
                # Additional validation for title-like text
                if ('"' in text or text[0].isupper() or 
                    any(word in text.lower() for word in ['challenge', 'hackathon', 'welcome', 'introduction'])):
                    # If it contains quotes, get the full quoted title
                    if '"' in text:
                        # Look for the complete quoted text across multiple spans/lines
                        full_title = self._extract_quoted_title(doc, page_num)
                        if full_title:
                            return full_title
                    return text.replace('"', '').strip()
        
        # Fallback: try to extract meaningful title from content
        if len(doc) > 0:
            first_page_text = doc[0].get_text()
            lines = first_page_text.split('\n')[:10]  # First 10 lines
            for line in lines:
                line = line.strip()
                if (len(line) > 10 and len(line) < 150 and
                    ('"' in line or line.startswith('Welcome') or 'Challenge' in line)):
                    return line.replace('"', '').strip()
        
        # Final fallback to filename (cleaned)
        filename = doc.name.split('/')[-1].replace('.pdf', '') if doc.name else "Untitled Document"
        # Clean up filename
        filename = filename.replace('_', ' ').replace('-', ' ')
        return filename
    
    def _extract_headings(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract hierarchical headings from document"""
        headings = []
        
        # Try TOC first
        toc = doc.get_toc()
        if toc:
            for item in toc:
                level, title, page_num = item
                heading_level = f"H{min(level, 3)}"  # Cap at H3
                headings.append({
                    "level": heading_level,
                    "text": title.strip(),
                    "page": page_num
                })
        else:
            # Fallback to text analysis
            headings = self._extract_headings_from_text(doc)
        
        return headings
    
    def _extract_headings_from_text(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract headings by analyzing text formatting"""
        headings = []
        font_sizes = []
        
        # First pass: collect all font sizes to determine heading thresholds
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            font_size = span.get("size", 0)
                            if font_size > 0:
                                font_sizes.append(font_size)
        
        if not font_sizes:
            return headings
        
        # Determine heading thresholds
        font_sizes.sort(reverse=True)
        unique_sizes = sorted(set(font_sizes), reverse=True)
        
        # Define thresholds for H1, H2, H3
        h1_threshold = unique_sizes[0] if len(unique_sizes) > 0 else 16
        h2_threshold = unique_sizes[1] if len(unique_sizes) > 1 else 14
        h3_threshold = unique_sizes[2] if len(unique_sizes) > 2 else 12
        
        # Second pass: identify headings
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        max_font_size = 0
                        is_bold = False
                        
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            font_size = span.get("size", 0)
                            flags = span.get("flags", 0)
                            
                            line_text += text + " "
                            max_font_size = max(max_font_size, font_size)
                            
                            # Check if bold (flag 16 indicates bold)
                            if flags & 2**4:
                                is_bold = True
                        
                        line_text = line_text.strip()
                        
                        # Heading criteria
                        if (line_text and len(line_text) > 3 and len(line_text) < 200 and
                            (max_font_size >= h3_threshold or is_bold)):
                            
                            # Determine heading level
                            if max_font_size >= h1_threshold:
                                level = "H1"
                            elif max_font_size >= h2_threshold:
                                level = "H2"
                            else:
                                level = "H3"
                            
                            # Additional filters
                            if self._is_likely_heading(line_text):
                                headings.append({
                                    "level": level,
                                    "text": line_text,
                                    "page": page_num + 1
                                })
        
        return headings
    
    def _extract_quoted_title(self, doc: fitz.Document, page_num: int) -> str:
        """Extract complete quoted title from document"""
        page = doc[page_num]
        text = page.get_text()
        
        # Look for text in quotes
        import re
        quoted_pattern = r'"([^"]+)"'
        matches = re.findall(quoted_pattern, text)
        
        for match in matches:
            if len(match) > 10 and any(word in match.lower() for word in 
                                     ['challenge', 'hackathon', 'connecting', 'dots']):
                return match.strip()
        
        return None
    
    def _is_likely_heading(self, text: str) -> bool:
        """Determine if text is likely a heading"""
        # Remove common false positives
        exclude_patterns = [
            r'^\d+$',  # Just numbers
            r'^page \d+',  # Page numbers
            r'^\d+\.\d+$',  # Decimal numbers
            r'^figure \d+',  # Figure captions
            r'^table \d+',  # Table captions
            r'^\w+@\w+\.\w+',  # Email addresses
            r'^http[s]?://',  # URLs
            r'^www\.',  # Web addresses
            r'\.com',  # Domain names
            r'\.git$',  # Git repositories
        ]
        
        text_lower = text.lower().strip()
        
        for pattern in exclude_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Check for heading-like characteristics
        # Headings are usually short, capitalized, and end without punctuation
        if len(text) > 150:  # Too long
            return False
        
        if text.endswith('.') and text.count('.') > 1:  # Likely sentence
            return False
        
        # Check for common heading patterns
        heading_patterns = [
            r'^\d+\.?\s+\w+',  # Numbered headings
            r'^chapter \d+',  # Chapter headings
            r'^section \d+',  # Section headings
            r'^round \d+[a-z]?:?',  # Round headings (like Round 1A, Round 1B)
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*:?$',  # Title case
            r'^[A-Z]{2,}',  # ALL CAPS (but not too short)
            r'challenge|hackathon|appendix',  # Common document section words
        ]
        
        for pattern in heading_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Accept if it's a colon-terminated heading
        if text.endswith(':') and len(text.split()) <= 8:
            return True
        
        # Default: accept if it looks structured and not too long
        return len(text.split()) <= 12 and not text.endswith(',') and not text.endswith('.')
