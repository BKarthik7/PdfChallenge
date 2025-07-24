"""
PDF Processing utilities for extracting text and structure
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import fitz  # PyMuPDF
import re

class PDFProcessor:
    """Handles PDF text extraction and preprocessing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_full_content(self, pdf_path: Path) -> Dict[int, Dict[str, Any]]:
        """Extract full content from PDF with page-level organization"""
        try:
            doc = fitz.open(str(pdf_path))
            content = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text with formatting information
                text_dict = page.get_text("dict")
                plain_text = page.get_text()
                
                # Process and clean text
                cleaned_text = self._clean_text(plain_text)
                
                # Extract images and tables info (basic)
                images = self._extract_image_info(page)
                tables = self._detect_tables(text_dict)
                
                content[page_num + 1] = {
                    'text': cleaned_text,
                    'raw_text': plain_text,
                    'formatting': text_dict,
                    'images': images,
                    'tables': tables,
                    'word_count': len(cleaned_text.split())
                }
            
            doc.close()
            self.logger.info(f"Extracted content from {len(content)} pages")
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {pdf_path}: {str(e)}")
            raise
    
    def extract_text_with_formatting(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extract text with detailed formatting information"""
        try:
            doc = fitz.open(str(pdf_path))
            formatted_content = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                page_content = {
                    'page': page_num + 1,
                    'blocks': []
                }
                
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        block_text = ""
                        block_info = {
                            'text': '',
                            'bbox': block.get('bbox', []),
                            'lines': []
                        }
                        
                        for line in block["lines"]:
                            line_text = ""
                            line_info = {
                                'text': '',
                                'spans': []
                            }
                            
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                line_text += text
                                
                                span_info = {
                                    'text': text,
                                    'font': span.get("font", ""),
                                    'size': span.get("size", 0),
                                    'flags': span.get("flags", 0),
                                    'color': span.get("color", 0),
                                    'bbox': span.get("bbox", [])
                                }
                                line_info['spans'].append(span_info)
                            
                            line_info['text'] = line_text
                            block_info['lines'].append(line_info)
                            block_text += line_text + "\n"
                        
                        block_info['text'] = block_text.strip()
                        page_content['blocks'].append(block_info)
                
                formatted_content.append(page_content)
            
            doc.close()
            return formatted_content
            
        except Exception as e:
            self.logger.error(f"Error extracting formatted text from {pdf_path}: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Fix common OCR issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)  # Fix hyphenated words across lines
        
        # Remove page numbers and headers/footers (basic)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip likely page numbers
            if re.match(r'^\d+$', line):
                continue
            
            # Skip very short lines that might be artifacts
            if len(line) < 3:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_image_info(self, page) -> List[Dict[str, Any]]:
        """Extract basic information about images on the page"""
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                image_info = {
                    'index': img_index,
                    'width': base_image.get('width', 0),
                    'height': base_image.get('height', 0),
                    'ext': base_image.get('ext', ''),
                    'size': len(base_image.get('image', b''))
                }
                images.append(image_info)
                
            except Exception as e:
                self.logger.warning(f"Could not extract image {img_index}: {str(e)}")
                continue
        
        return images
    
    def _detect_tables(self, text_dict: Dict) -> List[Dict[str, Any]]:
        """Basic table detection based on text layout"""
        tables = []
        
        # Simple heuristic: look for aligned text blocks that might be tables
        # This is a basic implementation and could be improved
        
        blocks = text_dict.get("blocks", [])
        potential_table_blocks = []
        
        for block in blocks:
            if "lines" in block:
                lines = block["lines"]
                if len(lines) > 2:  # At least 3 lines
                    # Check for consistent alignment
                    x_positions = []
                    for line in lines:
                        for span in line.get("spans", []):
                            bbox = span.get("bbox", [])
                            if bbox:
                                x_positions.append(bbox[0])
                    
                    # If we have multiple consistent x-positions, might be a table
                    if len(set(round(x, -1) for x in x_positions)) > 2:
                        table_info = {
                            'bbox': block.get('bbox', []),
                            'estimated_columns': len(set(round(x, -1) for x in x_positions)),
                            'estimated_rows': len(lines)
                        }
                        tables.append(table_info)
        
        return tables
    
    def get_document_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract document metadata"""
        try:
            doc = fitz.open(str(pdf_path))
            metadata = doc.metadata
            
            # Add additional computed metadata
            metadata['page_count'] = len(doc)
            metadata['file_size'] = pdf_path.stat().st_size
            
            doc.close()
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {str(e)}")
            return {}
