"""
Round 1B: Persona-Driven Document Intelligence
Analyzes document collections based on persona and job-to-be-done requirements
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

from pdf_processor import PDFProcessor
from nlp_analyzer import NLPAnalyzer
from utils import is_pdf_file

class Round1BProcessor:
    """Processes document collections for persona-driven analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pdf_processor = PDFProcessor()
        self.nlp_analyzer = NLPAnalyzer()
    
    def process_directory(self, input_dir: str, output_dir: str, persona: str, job: str) -> None:
        """Process all PDFs in directory for persona-driven analysis"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        pdf_files = [f for f in input_path.iterdir() if is_pdf_file(f)]
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {input_dir}")
            return
        
        if len(pdf_files) < 3 or len(pdf_files) > 10:
            self.logger.warning(f"Expected 3-10 PDFs, found {len(pdf_files)}")
        
        self.logger.info(f"Processing {len(pdf_files)} PDFs for persona analysis")
        
        try:
            result = self.analyze_documents(pdf_files, persona, job)
            
            # Save result
            output_file = output_path / "challenge1b_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved analysis to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to process documents: {str(e)}")
            raise
    
    def analyze_documents(self, pdf_files: List[Path], persona: str, job: str) -> Dict[str, Any]:
        """Analyze documents based on persona and job requirements"""
        # Extract content from all documents
        documents_content = []
        
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Extracting content from {pdf_file.name}")
                content = self.pdf_processor.extract_full_content(pdf_file)
                documents_content.append({
                    'file': pdf_file.name,
                    'content': content
                })
            except Exception as e:
                self.logger.error(f"Failed to extract content from {pdf_file.name}: {str(e)}")
                continue
        
        if not documents_content:
            raise ValueError("No documents could be processed")
        
        # Analyze relevance and extract sections
        relevant_sections = self._extract_relevant_sections(documents_content, persona, job)
        
        # Generate subsection analysis
        subsections = self._analyze_subsections(relevant_sections, persona, job)
        
        # Prepare output
        result = {
            "metadata": {
                "input_documents": [doc['file'] for doc in documents_content],
                "persona": persona,
                "job_to_be_done": job,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": relevant_sections,
            "subsection_analysis": subsections
        }
        
        return result
    
    def _extract_relevant_sections(self, documents_content: List[Dict], persona: str, job: str) -> List[Dict[str, Any]]:
        """Extract and rank sections based on relevance to persona and job"""
        all_sections = []
        
        # Extract sections from each document
        for doc in documents_content:
            sections = self._identify_sections(doc['content'], doc['file'])
            all_sections.extend(sections)
        
        # Score sections based on relevance
        scored_sections = []
        for section in all_sections:
            relevance_score = self.nlp_analyzer.calculate_relevance(
                section['text'], persona, job
            )
            
            scored_sections.append({
                "document": section['document'],
                "page_number": section['page'],
                "section_title": section['title'],
                "importance_rank": relevance_score,
                "text": section['text'][:500]  # Truncate for output
            })
        
        # Sort by relevance and return top sections
        scored_sections.sort(key=lambda x: x['importance_rank'], reverse=True)
        
        # Assign ranks
        for i, section in enumerate(scored_sections[:20]):  # Top 20 sections
            section['importance_rank'] = i + 1
        
        return scored_sections[:20]
    
    def _identify_sections(self, content: Dict, document_name: str) -> List[Dict[str, Any]]:
        """Identify sections within document content"""
        sections = []
        
        for page_num, page_content in content.items():
            # Split page into potential sections
            text = page_content.get('text', '')
            
            # Look for section markers
            section_patterns = [
                r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
                r'^\d+\.?\s+[A-Z].*',  # Numbered sections
                r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s*$',  # Title case
                r'^(Chapter|Section|Part)\s+\d+',  # Explicit chapters/sections
            ]
            
            lines = text.split('\n')
            current_section = {"title": "Introduction", "text": "", "start_line": 0}
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line is a section header
                is_header = False
                for pattern in section_patterns:
                    if re.match(pattern, line) and len(line) < 100:
                        is_header = True
                        break
                
                if is_header and current_section["text"]:
                    # Save previous section
                    if len(current_section["text"]) > 100:  # Minimum section length
                        sections.append({
                            "document": document_name,
                            "page": page_num,
                            "title": current_section["title"],
                            "text": current_section["text"].strip()
                        })
                    
                    # Start new section
                    current_section = {
                        "title": line,
                        "text": "",
                        "start_line": i
                    }
                else:
                    current_section["text"] += line + " "
            
            # Add final section
            if current_section["text"] and len(current_section["text"]) > 100:
                sections.append({
                    "document": document_name,
                    "page": page_num,
                    "title": current_section["title"],
                    "text": current_section["text"].strip()
                })
        
        return sections
    
    def _analyze_subsections(self, sections: List[Dict], persona: str, job: str) -> List[Dict[str, Any]]:
        """Analyze subsections and refine text based on persona needs"""
        subsections = []
        
        for section in sections[:10]:  # Top 10 sections for subsection analysis
            # Extract key subsections
            text = section.get('text', '')
            key_points = self._extract_key_points(text, persona, job)
            
            for i, point in enumerate(key_points):
                refined_text = self.nlp_analyzer.refine_text_for_persona(point, persona, job)
                
                subsections.append({
                    "document": section['document'],
                    "page_number": section['page_number'],
                    "refined_text": refined_text,
                    "relevance_score": len(key_points) - i  # Simple scoring
                })
        
        # Sort by relevance
        subsections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return subsections[:15]  # Return top 15 subsections
    
    def _extract_key_points(self, text: str, persona: str, job: str) -> List[str]:
        """Extract key points from text relevant to persona and job"""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Score sentences based on relevance
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Minimum sentence length
                score = self.nlp_analyzer.calculate_relevance(sentence, persona, job)
                scored_sentences.append((sentence, score))
        
        # Sort by score and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scored_sentences[:5]]  # Top 5 sentences per section
