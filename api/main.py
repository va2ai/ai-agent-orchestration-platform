from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.routes import sessions, refinement, websocket, upload
from pathlib import Path

app = FastAPI(
    title="PRD Refinement API",
    description="API for automated PRD quality improvement",
    version="1.0.0"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
ui_static = Path(__file__).parent.parent / "ui" / "static"
ui_static.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(ui_static)), name="static")

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(refinement.router, prefix="/api/refinement", tags=["Refinement"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(upload.router, prefix="/api/files", tags=["Files"])

# Serve dashboard
@app.get("/")
async def dashboard():
    ui_index = Path(__file__).parent.parent / "ui" / "index.html"
    if ui_index.exists():
        return FileResponse(ui_index)
    return {"message": "Dashboard not yet available. Use /docs for API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# File upload endpoint (added directly to avoid import issues)
from fastapi import UploadFile, File
@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and extract text content"""
    try:
        content_bytes = await file.read()
        filename = file.filename.lower()

        if filename.endswith(('.txt', '.md')):
            text = content_bytes.decode('utf-8')
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
            except ImportError:
                return {"detail": "PDF support not installed. Install with: pip install PyPDF2"}
        elif filename.endswith('.docx'):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(content_bytes))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n\n"
            except ImportError:
                return {"detail": "DOCX support not installed. Install with: pip install python-docx"}
        else:
            try:
                text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return {"detail": f"Unsupported file format: {file.filename}"}

        return {
            "success": True,
            "filename": file.filename,
            "content": text,
            "length": len(text)
        }
    except Exception as e:
        return {"detail": f"Error processing file: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
