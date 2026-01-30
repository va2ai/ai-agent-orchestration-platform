#!/usr/bin/env python3
"""
File upload endpoint
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import tempfile
from pathlib import Path

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and extract text content.

    Supports:
    - Text files (.txt, .md)
    - PDF files (.pdf)
    - Word documents (.docx)
    - Plain text in any format
    """

    try:
        # Read file content
        content = await file.read()

        # Determine file type and extract text
        filename = file.filename.lower()

        if filename.endswith(('.txt', '.md')):
            # Plain text or markdown
            text = content.decode('utf-8')

        elif filename.endswith('.pdf'):
            # PDF extraction
            try:
                import PyPDF2
                import io

                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"

            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="PDF support not installed. Install with: pip install PyPDF2"
                )

        elif filename.endswith('.docx'):
            # Word document extraction
            try:
                from docx import Document
                import io

                doc = Document(io.BytesIO(content))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n\n"

            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="DOCX support not installed. Install with: pip install python-docx"
                )

        else:
            # Try to decode as plain text
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {filename}. Supported: .txt, .md, .pdf, .docx"
                )

        return {
            "success": True,
            "filename": file.filename,
            "content": text,
            "length": len(text)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
