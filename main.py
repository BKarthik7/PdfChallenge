#!/usr/bin/env python3
"""
Main entry point for the PDF Intelligence System
Supports both Round 1A (structure extraction) and Round 1B (persona-driven analysis)
"""

import argparse
import sys
import os
import logging
from pathlib import Path
import json
import time

from round1a import Round1AProcessor
from round1b import Round1BProcessor
from utils import setup_logging, validate_input_directory

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='PDF Intelligence System')
    parser.add_argument('--round', choices=['1a', '1b'], default='1a',
                       help='Which round to execute (1a: structure extraction, 1b: persona analysis)')
    parser.add_argument('--input-dir', default='/app/input',
                       help='Input directory containing PDFs')
    parser.add_argument('--output-dir', default='/app/output',
                       help='Output directory for results')
    parser.add_argument('--persona', type=str,
                       help='Persona definition for Round 1B')
    parser.add_argument('--job', type=str,
                       help='Job-to-be-done for Round 1B')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # Validate input directory
    if not validate_input_directory(args.input_dir):
        logger.error(f"Input directory {args.input_dir} does not exist or contains no PDFs")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        if args.round == '1a':
            logger.info("Starting Round 1A: PDF Structure Extraction")
            processor = Round1AProcessor()
            processor.process_directory(args.input_dir, args.output_dir)
            
        elif args.round == '1b':
            logger.info("Starting Round 1B: Persona-Driven Document Intelligence")
            
            # Check for persona and job parameters
            if not args.persona or not args.job:
                # Try to read from persona.json and job.json in input directory
                persona_file = Path(args.input_dir) / "persona.json"
                job_file = Path(args.input_dir) / "job.json"
                
                if persona_file.exists() and job_file.exists():
                    with open(persona_file, 'r') as f:
                        persona_data = json.load(f)
                        args.persona = persona_data.get('persona', '')
                    
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                        args.job = job_data.get('job', '')
                else:
                    logger.error("Round 1B requires persona and job parameters or persona.json/job.json files")
                    sys.exit(1)
            
            processor = Round1BProcessor()
            processor.process_directory(args.input_dir, args.output_dir, args.persona, args.job)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"Processing completed successfully in {processing_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
