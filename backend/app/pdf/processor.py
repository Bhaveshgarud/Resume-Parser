# app/pdf/processor.py
from .parser import PDFParser, FormField
from .extractor import PDFTextExtractor
from typing import Dict, List, Tuple
import re
from .skills_processor import SkillsProcessor
import spacy

class PDFProcessor:
    def __init__(self, pdf_content: bytes):
        self.parser = PDFParser(pdf_content)
        self.extractor = PDFTextExtractor(self.parser)
        self.skills_processor = SkillsProcessor()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import en_core_web_sm
            self.nlp = en_core_web_sm.load()

    def process(self) -> Dict:
        # Extract form fields and sections
        form_fields = self.parser.extract_form_fields()
        text_sections = self.extractor.extract_text_by_sections()
        
        # Process sections for structured data
        processed_sections = {}
        for section_name, content in text_sections.items():
            confidence = 0.95 if len(content) > 50 else 0.5
            processed_sections[section_name] = {
                "content": content,
                "confidence": confidence
            }
        
        # Process skills if present in form fields
        skills_field = next((field for field in form_fields if field.type == 'skills'), None)
        if skills_field and skills_field.value:
            skills_analysis = self.skills_processor.categorize_skills(skills_field.value)
            processed_sections['skills_analysis'] = {
                "content": str(skills_analysis),
                "confidence": 0.9
            }
        
        return {
            'fields': form_fields,
            'sections': processed_sections
        }

    def get_field_suggestions(self, fields: List[FormField]) -> Dict[str, List[str]]:
        suggestions = {}
        text_sections = self.extractor.extract_text_by_sections()
        
        for field in fields:
            if field.type == 'name':
                suggestions[field.name] = self._extract_names(text_sections)
            elif field.type == 'email':
                suggestions[field.name] = self._extract_emails(text_sections)
            elif field.type == 'skills':
                suggestions[field.name] = self._extract_skills(text_sections)
        
        return suggestions

    def _extract_names(self, sections: Dict[str, str]) -> List[str]:
        names = []
        header_text = sections.get('header', '')
        doc = self.nlp(header_text)
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                names.append(ent.text)
        return names[:1]  # Return only the first name found

    def _extract_emails(self, sections: Dict[str, str]) -> List[str]:
        emails = []
        text = " ".join(sections.values())
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(email_pattern, text)
        emails.extend(match.group() for match in matches)
        return emails

    def _extract_skills(self, sections: Dict[str, str]) -> List[str]:
        skills_text = sections.get('skills', '')
        if skills_text:
            return list(self.skills_processor.categorize_skills(skills_text).values())
        return []