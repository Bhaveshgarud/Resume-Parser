# api/models/pdf.py
from pydantic import BaseModel
from typing import Dict, List, Optional

class FieldMatch(BaseModel):
    field_name: str
    confidence: float
    suggested_value: str

class Section(BaseModel):
    content: str
    confidence: float

class ProcessedPdfResponse(BaseModel):
    matched_fields: List[FieldMatch]
    sections: Dict[str, Section]
    processing_time: float
