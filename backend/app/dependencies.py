 
# dependencies.py
from fastapi import HTTPException, UploadFile
from typing import Annotated
import fitz  # PyMuPDF

async def verify_pdf_file(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are allowed")
    return file

PdfFile = Annotated[UploadFile, verify_pdf_file]