# PDF Intelligence System

A comprehensive solution for Adobe's "Connecting the Dots" hackathon challenge, implementing both Round 1A (PDF structure extraction) and Round 1B (persona-driven document intelligence).

## Overview

This system processes PDF documents to extract structured information and provide intelligent analysis based on user personas and specific job requirements.

### Features

**Round 1A - PDF Structure Extraction:**
- Extracts document titles and hierarchical headings (H1, H2, H3)
- Outputs structured JSON with heading levels and page numbers
- Processes files in under 10 seconds per 50-page PDF
- Works offline without internet access

**Round 1B - Persona-Driven Document Intelligence:**
- Processes collections of 3-10 related PDFs
- Analyzes content based on specific personas and job requirements
- Extracts and ranks relevant sections
- Provides subsection analysis with refined text

## Architecture

The system is built with a modular architecture:

- `main.py`: Entry point and command-line interface
- `round1a.py`: PDF structure extraction logic
- `round1b.py`: Persona-driven analysis logic
- `pdf_processor.py`: PDF text extraction utilities
- `nlp_analyzer.py`: Natural language processing and relevance scoring
- `utils.py`: Common utilities and helper functions

## Technical Stack

- **Python 3.9+**: Core language
- **PyMuPDF (fitz)**: PDF processing and text extraction
- **NLTK**: Natural language processing
- **scikit-learn**: Text similarity and machine learning utilities
- **Docker**: Containerization for consistent deployment

## Installation & Usage

### Docker Execution (Production Ready)

1. **Build the Docker image:**
   ```bash
   docker build --platform linux/amd64 -t pdf-intelligence:latest .
   ```

2. **Run Round 1A (Structure Extraction):**
   ```bash
   docker run --rm \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/output:/app/output \
     --network none \
     pdf-intelligence:latest
   ```

3. **Run Round 1B (Persona Analysis with files):**
   ```bash
   # Place persona.json and job.json in input directory, then:
   docker run --rm \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/output:/app/output \
     --network none \
     pdf-intelligence:latest \
     python main.py --round 1b --input-dir /app/input --output-dir /app/output
   ```

4. **Run Round 1B (Persona Analysis with parameters):**
   ```bash
   docker run --rm \
     -v $(pwd)/input:/app/input \
     -v $(pwd)/output:/app/output \
     --network none \
     pdf-intelligence:latest \
     python main.py --round 1b --persona "PhD Researcher in AI" --job "Literature review on neural networks"
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   pip install PyMuPDF nltk scikit-learn numpy scipy
   ```

2. **Download NLTK data:**
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

3. **Run the application:**
   ```bash
   python main.py --round 1a --input-dir ./input --output-dir ./output
   ```

## Input/Output Formats

### Round 1A Input
- PDF files in the input directory
- Maximum 50 pages per PDF

### Round 1A Output
```json
{
  "title": "Connecting the Dots Challenge",
  "outline": [
    {"level": "H1", "text": "Welcome to the \"Connecting the Dots\" Challenge", "page": 2},
    {"level": "H1", "text": "Round 1A: Understand Your Document", "page": 3},
    {"level": "H1", "text": "Round 1B: Persona-Driven Document Intelligence", "page": 7}
  ]
}
```

### Round 1B Input Files
- `persona.json`: Contains persona definition
- `job.json`: Contains job-to-be-done description
- Multiple PDF files (3-10 recommended)

### Round 1B Output
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "PhD Researcher in Computational Biology",
    "job_to_be_done": "Prepare comprehensive literature review",
    "processing_timestamp": "2025-07-24T09:16:51.139541"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "page_number": 7,
      "section_title": "Academic Research",
      "importance_rank": 1,
      "text": "Research papers on Graph Neural Networks..."
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf", 
      "page_number": 7,
      "refined_text": "Key methodologies for document intelligence...",
      "relevance_score": 5
    }
  ]
}
