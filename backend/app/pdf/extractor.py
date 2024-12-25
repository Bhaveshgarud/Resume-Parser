# app/pdf/extractor.py
from typing import Dict, List, Optional
import fitz
import re
import os
import requests
import json

class PDFTextExtractor:
    def __init__(self, parser):
        self.parser = parser
        self.section_patterns = {
            'experience': [
                r'(?i)^work\s*experience',
                r'(?i)^professional\s*experience',
                r'(?i)^employment\s*history'
            ],
            'education': [
                r'(?i)^education',
                r'(?i)^academic\s*background',
                r'(?i)^qualifications'
            ],
            'skills': [
                r'(?i)^skills',
                r'(?i)^technical\s*skills',
                r'(?i)^competencies'
            ]
        }
        
    def extract_text_by_sections(self) -> Dict[str, str]:
        sections = {}
        current_section = "header"
        
        for page_num, page in enumerate(self.parser.doc):
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if self._is_header_or_footer(block):
                    continue
                    
                text = self._extract_block_text(block)
                section = self._identify_section(text)
                
                if section:
                    current_section = section
                    sections[current_section] = sections.get(current_section, "")
                else:
                    sections[current_section] = sections.get(current_section, "") + "\n" + text
                    
        return self._post_process_sections(sections)
        
    def _post_process_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Clean up and normalize extracted sections."""
        processed = {}
        for section, content in sections.items():
            # Remove extra whitespace and normalize
            cleaned = re.sub(r'\s+', ' ', content).strip()
            # Remove section headers from content
            for pattern_list in self.section_patterns.values():
                for pattern in pattern_list:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            if cleaned:  # Only include non-empty sections
                processed[section] = cleaned
        return processed
        
    def _identify_section(self, text: str) -> Optional[str]:
        for section, patterns in self.section_patterns.items():
            if any(re.search(pattern, text.strip()) for pattern in patterns):
                return section
        return None
        
    def _is_header_or_footer(self, block: Dict) -> bool:
        # Check if block is at top or bottom of page
        y_pos = block.get("bbox", [0, 0, 0, 0])[1]
        page_height = self.parser.doc[0].rect.height
        return y_pos < 50 or y_pos > page_height - 50
    
    def _extract_block_text(self, block: Dict) -> str:
        return " ".join(
            span["text"] 
            for line in block.get("lines", []) 
            for span in line.get("spans", [])
        )

def test_pdf_processing():
    url = "http://localhost:8000/api/v1/pdf/process"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(current_dir, "sample_pdfs", "Bhavesh-Garud-5th.pdf")
    
    try:
        # First verify we can open the PDF
        doc = fitz.open(pdf_path)
        print(f"PDF loaded successfully. Pages: {len(doc)}")
        
        # Try the API request
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            result = response.json()
            print("\nProcessed PDF Results:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error {response.status_code}:")
            print(response.text)
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise

if __name__ == "__main__":
    test_pdf_processing()
