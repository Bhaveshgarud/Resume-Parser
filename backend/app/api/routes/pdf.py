# app/api/routes/pdf.py
from fastapi import APIRouter, HTTPException
from ..models.pdf import ProcessedPdfResponse, FieldMatch, Section
from ...pdf.processor import PDFProcessor
from ...dependencies import PdfFile
import time

router = APIRouter()

@router.post("/process", response_model=ProcessedPdfResponse)
async def process_pdf(file: PdfFile):
    try:
        start_time = time.time()
        
        # Read and process PDF
        content = await file.read()
        processor = PDFProcessor(content)
        result = processor.process()
        
        # Convert to response model
        matched_fields = [
            FieldMatch(
                field_name=field.type,
                confidence=0.95 if field.value else 0.5,
                suggested_value=field.value or ""
            )
            for field in result['fields']
        ]
        
        # Format sections
        sections = {
            name: Section(
                content=data["content"],
                confidence=data["confidence"]
            )
            for name, data in result['sections'].items()
        }
        
        return ProcessedPdfResponse(
            matched_fields=matched_fields,
            sections=sections,
            processing_time=time.time() - start_time
        )
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise HTTPException(500, f"PDF processing error: {str(e)}")