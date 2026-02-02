# Goal Field & File Upload Features

## Overview

Added two powerful new features to make the dynamic roundtable system even more targeted and convenient:

1. **Goal Field** - Specify what the roundtable should accomplish
2. **File Upload** - Upload documents instead of pasting content

## 1. Goal Field

### Purpose
The goal field tells the AI what outcome you want from the roundtable discussion. This helps the meta-orchestrator generate more targeted expert participants.

### How It Works

**Without Goal:**
- User: "VA Rating Decision"
- AI generates: Generic reviewers (e.g., Legal Expert, Medical Reviewer, Policy Analyst)

**With Goal:**
- User: "VA Rating Decision"
- Goal: "Write a comprehensive appeal"
- AI generates: **Appeal-focused experts** (e.g., Veterans Law Attorney, Medical Evidence Specialist, Appeals Writer)

### Examples

#### Example 1: VA Rating Decision Appeal
```json
{
  "title": "VA Rating Decision for PTSD Claim",
  "goal": "Write a comprehensive appeal challenging the denial",
  "document_type": "legal",
  "num_participants": 3
}
```

**AI Generates:**
- Veterans Law Attorney (appeals strategy, legal precedents)
- Clinical Psychologist (medical evidence, PTSD criteria)
- VA Appeals Specialist (procedural requirements, evidence standards)

#### Example 2: PRD Improvement
```json
{
  "title": "Mobile App Feature PRD",
  "goal": "Improve clarity and add success metrics",
  "document_type": "prd",
  "num_participants": 3
}
```

**AI Generates:**
- Product Manager (clarity, user stories, success metrics)
- UX Researcher (user experience metrics, testing criteria)
- Data Analyst (quantifiable metrics, tracking implementation)

#### Example 3: Code Security
```json
{
  "title": "Authentication System Review",
  "goal": "Add security measures and fix vulnerabilities",
  "document_type": "code-review",
  "num_participants": 4
}
```

**AI Generates:**
- Security Architect (threat modeling, security patterns)
- Cryptography Expert (encryption, token management)
- Penetration Tester (vulnerability assessment)
- Compliance Officer (regulatory requirements)

#### Example 4: Business Plan
```json
{
  "title": "SaaS Product Launch Strategy",
  "goal": "Create go-to-market plan and pricing strategy",
  "document_type": "business-strategy",
  "num_participants": 4
}
```

**AI Generates:**
- Marketing Strategist (GTM strategy, positioning)
- Pricing Analyst (pricing models, competitive analysis)
- Sales Director (sales channels, customer acquisition)
- Financial Planner (revenue projections, unit economics)

### API Changes

**New Field in `StartRefinementRequest`:**
```python
goal: Optional[str] = Field(
    default=None,
    description="What the roundtable should accomplish"
)
```

**Examples:**
- "write an appeal"
- "improve clarity"
- "add security measures"
- "create pricing strategy"
- "identify technical risks"
- "make it production-ready"

### UI Changes

**New Input Field:**
```html
<label>Goal (Optional)</label>
<input id="goal" placeholder="e.g., write an appeal, improve clarity, add security">
<p>What should the roundtable accomplish? AI will generate experts to help achieve this goal.</p>
```

### Implementation Details

**Meta-Orchestrator (`agents/meta_orchestrator.py`):**
- Added `goal` parameter to `generate_roundtable()`
- Includes goal in prompt: "Focus on participants who can help achieve this goal: {goal}"
- AI uses goal to select appropriate expert roles

**Dynamic Orchestrator (`orchestration/dynamic_orchestrator.py`):**
- Passes goal to meta-orchestrator
- Logs goal in refinement logs
- Includes goal in convergence report

**API (`api/services/dynamic_async_orchestrator.py`):**
- Accepts goal parameter in `run()`
- Broadcasts goal in session_created event
- Passes goal to participant generation

## 2. File Upload

### Purpose
Allows users to upload documents instead of manually copy-pasting content. Supports common document formats.

### Supported Formats

1. **Text Files** (`.txt`, `.md`)
   - Direct text extraction
   - Markdown preserved

2. **PDF Files** (`.pdf`)
   - Extracts text from all pages
   - Requires: `pip install PyPDF2`

3. **Word Documents** (`.docx`)
   - Extracts paragraphs
   - Requires: `pip install python-docx`

### How It Works

1. User clicks "Choose File" and selects document
2. User clicks "Upload" button
3. File sent to `/api/files/upload` endpoint
4. Server extracts text based on file type
5. Content populates textarea automatically
6. User can edit before submitting

### API Endpoint

**POST `/api/files/upload`**

**Request:**
```
multipart/form-data
file: <uploaded file>
```

**Response:**
```json
{
  "success": true,
  "filename": "va_decision.pdf",
  "content": "DEPARTMENT OF VETERANS AFFAIRS...",
  "length": 15234
}
```

**Error Cases:**
```json
{
  "detail": "PDF support not installed. Install with: pip install PyPDF2"
}
```

```json
{
  "detail": "Unsupported file format: file.xlsx. Supported: .txt, .md, .pdf, .docx"
}
```

### UI Implementation

**Upload Section:**
```html
<div class="mb-4">
  <label>Upload File (Optional)</label>
  <div class="flex gap-2">
    <input type="file" id="fileUpload" accept=".txt,.md,.pdf,.docx">
    <button type="button" id="uploadButton">Upload</button>
  </div>
  <p class="text-xs">Upload a text, markdown, PDF, or Word document</p>
  <p id="uploadStatus" class="text-xs hidden"></p>
</div>
```

**JavaScript Handler (`ui/static/js/app.js`):**
```javascript
document.getElementById('uploadButton').addEventListener('click', async () => {
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/files/upload', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  document.getElementById('content').value = data.content;
});
```

### Status Messages

**Uploading:**
- "Uploading..." (blue)

**Success:**
- "✓ Uploaded file.pdf (15,234 characters)" (green)
- Auto-hides after 3 seconds

**Error:**
- "✗ Upload failed: Unsupported file format" (red)

### File Upload Route (`api/routes/upload.py`)

**Key Features:**
- Detects file type by extension
- Graceful error handling
- Clear error messages
- Returns extracted text content

**PDF Extraction:**
```python
import PyPDF2
import io

pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
text = ""
for page in pdf_reader.pages:
    text += page.extract_text() + "\n\n"
```

**DOCX Extraction:**
```python
from docx import Document
import io

doc = Document(io.BytesIO(content))
text = ""
for paragraph in doc.paragraphs:
    text += paragraph.text + "\n\n"
```

## Use Case Example: VA Appeal

### Scenario
Veteran received a denial for PTSD claim and needs to write an appeal.

### Steps

1. **Upload Decision Letter**
   - Click "Choose File"
   - Select `va_rating_decision.pdf`
   - Click "Upload"
   - Content automatically populates

2. **Set Goal**
   - Title: "VA Rating Decision - PTSD Claim Denial"
   - Goal: "Write a comprehensive appeal challenging the denial"
   - Document Type: "legal"

3. **Generate Roundtable**
   - AI generates:
     - Veterans Law Attorney
     - Clinical Psychologist (PTSD specialist)
     - VA Appeals Expert

4. **Roundtable Discussion**
   - **Attorney**: Identifies legal errors, missing regulations, procedural issues
   - **Psychologist**: Assesses medical evidence gaps, suggests additional documentation
   - **Appeals Expert**: Reviews evidence standards, suggests supporting statements

5. **Moderator Refines**
   - Incorporates all feedback
   - Creates comprehensive appeal letter
   - Includes legal citations, medical evidence, procedural arguments

6. **Final Output**
   - Well-structured appeal letter
   - Addresses all denial reasons
   - Cites relevant regulations
   - Includes evidence checklist

## Benefits

### Goal Field Benefits

1. **More Targeted Experts**: AI generates participants specifically suited to the goal
2. **Better Outcomes**: Participants focus on achieving the stated goal
3. **Clear Direction**: Moderator knows what to optimize for
4. **Flexible**: Works with any document type or use case

### File Upload Benefits

1. **Convenience**: No more copy-pasting from PDFs
2. **Accuracy**: Preserves formatting and structure
3. **Speed**: Upload in seconds vs manual copying
4. **Supported Formats**: Works with common document types

## Installation Requirements

For full file upload support:

```bash
# PDF support
pip install PyPDF2

# Word document support
pip install python-docx
```

These are optional - basic `.txt` and `.md` files work without additional packages.

## API Documentation

Full API docs available at:
```
http://localhost:8000/docs
```

**New Endpoints:**
- `POST /api/files/upload` - Upload and extract file content
- `POST /api/refinement/start` (updated) - Now accepts `goal` parameter

## Future Enhancements

1. **OCR Support**: Extract text from scanned PDFs and images
2. **Excel/CSV**: Extract data from spreadsheets
3. **Batch Upload**: Upload multiple documents at once
4. **Goal Templates**: Pre-defined common goals (appeal, security audit, clarity improvement)
5. **File Preview**: Preview extracted content before submitting
6. **File History**: See recently uploaded files
7. **Direct URL**: Upload from URL instead of file

## Testing

### Test Goal Field

```bash
curl -X POST http://localhost:8000/api/refinement/start \
  -H "Content-Type: application/json" \
  -d '{
    "title": "VA Rating Decision",
    "content": "PTSD claim denied...",
    "goal": "Write a comprehensive appeal",
    "document_type": "legal",
    "num_participants": 3,
    "max_iterations": 2
  }'
```

### Test File Upload

```bash
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@document.pdf"
```

## Summary

✅ **Goal Field**
- Helps AI generate targeted experts
- Improves outcome quality
- Works with any document type
- Optional but recommended

✅ **File Upload**
- Supports `.txt`, `.md`, `.pdf`, `.docx`
- Auto-populates content textarea
- Clear status feedback
- Graceful error handling

Both features are **optional** and **backwards compatible** - existing workflows continue to work without changes.
