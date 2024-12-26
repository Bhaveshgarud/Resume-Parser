# app/pdf/parser.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import fitz
import re

@dataclass
class FormField:
    name: str
    type: str
    bbox: tuple
    page: int
    value: Optional[str] = None

class PDFParser:
    def __init__(self, pdf_content: bytes):
        self.doc = fitz.open(stream=pdf_content, filetype="pdf")
        self.field_patterns = {
            'full_name': [
                r'(?i)(?:^|\n|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?:\n|\s|$)',
                r'(?i)(?:name|candidate):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'phone': [
                r'(?<!\d)(\d{10})(?!\d)',
                r'(\+\d{1,3}[-.\s]?\d{10})'
            ],
            'location': [
                r'(?i)(?:location|address|city|based\s+in):\s*([^,\n]+(?:,\s*[^,\n]+){0,2})',
                r'(?i)(?:residing|living)\s+in\s+([^,\n]+)',
                r'(?i)(?:^|\n|\s)([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*)',
                r'(?i)(?:^|\n)Address[^\n]*?([^,\n]+(?:,\s*[^,\n]+){1,2})',
                r'(?i)\|\s*([^|,\n]+)\s*\|'
            ],
            'college_name': [
                r'(?i)(?:at|from|in)\s+((?:[A-Z][a-z\']+\s+)+(?:Engineering\s+)?(?:College|Polytechnic|Institute|University))',
                r'(?i)((?:[A-Z][a-z\']+\s+)+(?:Engineering\s+)?(?:College|Polytechnic|Institute|University))[^,\n]*',
                r'(?i)(?:Education|College|University):\s*((?:[A-Z][a-z\']+\s+)+(?:Engineering\s+)?(?:College|Polytechnic|Institute|University))',
            ],
            'Highest_Education': [
                r'(?i)B\.?E\.?\s+in\s+([^,\n]+)',
                r'(?i)Diploma\s+in\s+([^,\n]+)',
                r'(?i)(?:pursuing|completed)\s+([^,\n]+(?:Engineering|Technology))',
            ],
            'projects': [
                r'(?i)PROJECTS\s*(?:\n|\r\n)(.*?)(?=\n\s*(?:[A-Z][A-Z\s]+|$))',
                r'(?i)(?:^|\n)([^•\n]+)\s*(?:React\.js|HTML|CSS|JavaScript)[^\n]+',
            ],
            'education': [
                r'(?i)B\.?E\.?\s*(?:\([^)]+\))',
                r'(?i)(?:Bachelor|Master)[^,\n]+(?:Engineering|Technology|Science)[^,\n]+',
                r'(?i)Diploma\s+in\s+[^,\n]+',
            ],
            'graduation_year': [
                r'(?:19|20)\d{2}(?:\s*-\s*(?:Present|Current|\d{4}))',
                r'(?i)(?:Graduate|Pass|Completion|Graduation)\s*(?:Year|Date):\s*(\d{4})',
            ],
            'skills': [
                r'(?i)(?:Technical\s+)?Skills:\s*([^\n]+)',
                r'(?i)(?:Technologies|Programming\s+Languages):\s*([^\n]+)',
                r'(?i)PROGRAMMING\s+LANGUAGES\s*([^\n]+)',
                r'(?i)TECHNOLOGIES\s*([^\n]+)',
            ],
            'languages': [
                r'(?i)LANGUAGES\s*([^\n]+)'
            ]
        }

    def extract_form_fields(self) -> List[FormField]:
        fields = []
        all_text = ""
        
        # Extract text from all pages
        for page in self.doc:
            all_text += page.get_text() + "\n"
            
        # Clean the text
        all_text = self._clean_text(all_text)
        
        # Process each field type
        for field_type, patterns in self.field_patterns.items():
            value = self._extract_field_value(all_text, field_type, patterns)
            if value:
                fields.append(FormField(
                    name=field_type,
                    type=field_type,
                    bbox=(0, 0, 0, 0),
                    page=0,
                    value=value
                ))
        
        return fields

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with parsing
        text = re.sub(r'[|•]', '\n', text)
        # Normalize line endings
        text = re.sub(r'[\r\n]+', '\n', text)
        return text.strip()

    def _extract_field_value(self, text: str, field_type: str, patterns: List[str]) -> Optional[str]:
        values = []
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
            for match in matches:
                value = match.group(1) if match.groups() else match.group(0)
                value = value.strip()
                
                if field_type == 'skills':
                    skills = [s.strip() for s in re.split(r'[,\n]', value)]
                    values.extend(filter(None, skills))
                elif field_type == 'college_name':
                    value = re.sub(r'(?i)\s+(?:in|of|and)\s+.*$', '', value)
                    value = re.sub(r'\s+', ' ', value)
                    if re.search(r'(?i)(?:College|Polytechnic|Institute|University)', value):
                        values.append(value)
                elif field_type == 'course_name':
                    value = re.sub(r'(?i)^(?:B\.?E\.?\s+in\s+|Diploma\s+in\s+)', '', value)
                    value = re.sub(r'\s+', ' ', value)
                    values.append(value)
                elif field_type == 'projects':
                    value = re.sub(r'(?i)PROJECTS\s*', '', value)
                    value = re.sub(r'\s+', ' ', value)
                    projects = re.split(r'(?:\n|•)', value)
                    values.extend(p.strip() for p in projects if p.strip())
                elif field_type == 'location':
                    value = re.sub(r'(?i)(?:address|location|city):\s*', '', value)
                    value = re.sub(r'\s+', ' ', value)
                    parts = [p.strip() for p in value.split(',')]
                    if parts and re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', parts[0]):
                        values.append(parts[0])
                else:
                    values.append(value)

        if not values:
            return None
            
        if field_type == 'skills':
            return ', '.join(sorted(set(values)))
        elif field_type == 'projects':
            return ' | '.join(values)
        elif field_type in ['college_name', 'course_name']:
            return max(values, key=len) if values else None
        else:
            return values[0]

    def close(self):
        self.doc.close()