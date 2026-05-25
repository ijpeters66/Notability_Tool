# Notability-to-ServiceM8 Agent Specification

## Executive Summary

Build a hybrid web application that allows field service professionals (small teams of 2–5 people) to upload handwritten consultation notes from Notability PDFs, have an AI agent extract and interpret the data, review the extracted information in a web UI, and then automatically push structured data into ServiceM8 (job notes, client records, custom fields, attachments, task assignments).

**Architecture**: Hybrid (iPad → Notability PDF export → web app → OpenAI Responses API → ServiceM8 API)

**Deployment**: MVP-level (focus on core functionality; error handling and logging are secondary)

**Timeline**: 3–5 days to working prototype

---

## User Personas

### Primary: Field Service Professional (Small Team Lead)
- **Name**: Alex (electrician, plumber, HVAC tech, etc.)
- **Pain point**: Handwriting notes on iPad during consultation, then manually transcribing into ServiceM8 back at office
- **Goal**: Eliminate manual data entry; keep notes in own handwriting/format; reduce admin time
- **Tech comfort**: Moderate (uses iPad, ServiceM8, basic web apps)

---

## User Stories & Workflow

### Core Workflow

```
1. Consultant handwrites on iPad in Notability using PDF template + Apple Pencil
2. Exports PDF to Files/email
3. Opens web app, uploads PDF
4. Agent extracts data (handwriting → text → structured data)
5. Consultant reviews extracted data in web UI (with inline editing)
6. Consultant approves (or edits and re-approves)
7. Agent pushes data into ServiceM8 (job notes, client record, custom fields, attachments)
8. Success notification; user sees job updated in ServiceM8
```

### Multi-PDF Scenario

```
Consultant uploads 2 PDFs (initial notes + follow-up notes) for same job
→ Agent merges/concatenates extracted data
→ User reviews merged data
→ Single push to ServiceM8 (all data unified)
```

---

## Functional Requirements

### 1. PDF Upload & Storage
- **Input**: PDF file (any generic template, handwritten)
- **Storage**: Server-side (PostgreSQL blob or file system + DB reference)
- **Validation**: File size limit (10 MB), MIME type check
- **Persistence**: Store for audit trail (user can download/re-process)

### 2. Handwriting Recognition & Data Extraction
- **OCR Engine**: OpenAI API (vision) + text generation
  - Rationale: Vision-capable model for handwriting, diagrams, and structured extraction
  - Default model: `gpt-5-mini` for cost-conscious, well-defined extraction
  - Cost: ~$0.10–0.30 per consultation-sized PDF (acceptable MVP cost)
- **Process**:
  1. Convert PDF to images (one per page)
  2. Send images + extraction prompt to the OpenAI Responses API
  3. OpenAI returns structured JSON: `{ client_details, job_details, findings, recommendations, follow_up_actions, visual_notes, raw_text }`
- **Structured Output Schema**:
  ```json
  {
    "client_details": {
      "name": "string",
      "phone": "string",
      "email": "string",
      "address": "string"
    },
    "job_details": {
      "location": "string",
      "job_type": "string",
      "estimated_cost": "string or number"
    },
    "findings": [
      { "category": "string", "description": "string" }
    ],
    "recommendations": [
      { "action": "string", "priority": "high|medium|low", "estimated_effort": "string" }
    ],
    "follow_up_actions": [
      { "task": "string", "due_date": "string (optional)", "assigned_to": "string (optional)" }
    ],
    "raw_text": "string (full extracted text for fallback)"
  }
  ```

### 3. Review & Approval UI
- **Display**: Show extracted data in editable form
- **Editing**: Inline editing for each field (client details, findings, recommendations, etc.)
- **Preview**: Raw extracted text visible (so user can verify accuracy)
- **Actions**:
  - "Approve & Push to ServiceM8" → triggers agent to sync
  - "Edit & Re-Extract" → re-run OpenAI vision extraction on same PDF with feedback
  - "Cancel" → discard, return to upload
- **Multi-PDF handling**: Show merged data from multiple PDFs with source attribution (e.g., "Initial Notes" vs. "Follow-up")

### 4. ServiceM8 Integration
- **API**: ServiceM8 REST API (OAuth2 or API key)
- **Push Operations**:
  1. **Job Notes**: Create or append to existing job's notes
  2. **Client Record**: Update or create client with extracted details
  3. **Custom Fields**: Map extracted data to ServiceM8 custom fields (configurable mapping)
  4. **Attachments**: Upload extracted PDF + structured data summary as attachments
  5. **Task Assignments**: Create tasks from follow-up actions (if assignee specified)
- **Error Handling**: If push fails, show user error + allow retry
- **Audit**: Log all pushes (timestamp, user, job ID, data pushed)

### 5. Authentication & Authorization
- **Auth**: Simple email/password or Google OAuth (MVP level)
- **Multi-user**: Support 2–5 users per instance (small team)
- **Permissions**: All users can upload, review, approve (assume trusted team)
- **ServiceM8 API Key**: Store securely (environment variable or encrypted DB)

### 6. Data Model

**Tables**:
1. `users` (id, email, password_hash, name, created_at)
2. `consultations` (id, user_id, original_pdf_path, extracted_data_json, status: pending|approved|pushed|failed, created_at, updated_at)
3. `consultation_pushes` (id, consultation_id, servicem8_job_id, servicem8_client_id, push_timestamp, push_response_json)
4. `audit_log` (id, user_id, action, details, timestamp)

---

## Technical Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **OCR**: OpenAI API (vision + text-generation)
- **ServiceM8 API**: HTTP client (requests or httpx)
- **File Storage**: Local file system (uploaded PDFs) + PostgreSQL (extracted JSON)
- **PDF Processing**: pypdf or pdfplumber (for page extraction)
- **Image Conversion**: pdf2image (poppler-based)

### Frontend
- **Framework**: React + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks + context API (MVP level)
- **Form Handling**: React Hook Form
- **API Communication**: fetch or axios

### Deployment
- **Platform**: Railway.app or similar (paired with PostgreSQL add-on)
- **Environment**: Python 3.11+, Node.js 18+
- **Cost**: ~$40–60/month (includes DB, compute, bandwidth)

---

## API Endpoints (Backend)

### Authentication
- `POST /auth/register` — Create user account
- `POST /auth/login` — Login, return JWT
- `GET /auth/me` — Verify token, return current user

### Consultations (Core Workflow)
- `POST /consultations/upload` — Upload PDF, trigger extraction
  - Request: `{ file: File }`
  - Response: `{ consultation_id, extraction_status: "processing" }`
- `GET /consultations/{id}` — Get extracted data + approval UI data
  - Response: `{ consultation_id, extracted_data, status, pdf_url }`
- `PUT /consultations/{id}` — Update extracted data (user edits)
  - Request: `{ extracted_data: {...} }`
  - Response: `{ consultation_id, extracted_data }`
- `POST /consultations/{id}/approve` — Approve and push to ServiceM8
  - Request: `{ servicem8_job_id: string (optional) }`
  - Response: `{ consultation_id, status: "pushed", servicem8_response }`
- `POST /consultations/{id}/re-extract` — Re-run OpenAI vision extraction with feedback
  - Request: `{ feedback: string }`
  - Response: `{ consultation_id, extraction_status: "processing", new_extracted_data }`

### Consultations (Management)
- `GET /consultations` — List all consultations (with pagination)
- `DELETE /consultations/{id}` — Delete consultation + PDF

### ServiceM8 Configuration
- `GET /config/servicem8` — Get current ServiceM8 integration status
- `POST /config/servicem8` — Set up ServiceM8 API key (one-time, admin only)

---

## Extraction Prompt (OpenAI API)

```
You are an expert at reading handwritten consultation notes from field service professionals.

Given the following PDF pages of handwritten notes, extract and structure the data into JSON.

Follow this schema exactly:
{
  "client_details": {
    "name": "extracted client name or null",
    "phone": "extracted phone number or null",
    "email": "extracted email or null",
    "address": "extracted address or null"
  },
  "job_details": {
    "location": "extracted job location or null",
    "job_type": "extracted type of work or null",
    "estimated_cost": "extracted cost estimate or null"
  },
  "findings": [
    { "category": "category name", "description": "what was found/observed" }
  ],
  "recommendations": [
    { "action": "recommended action", "priority": "high|medium|low", "estimated_effort": "time estimate or null" }
  ],
  "follow_up_actions": [
    { "task": "task description", "due_date": "date or null", "assigned_to": "person or null" }
  ],
  "raw_text": "full extracted text from the notes"
}

Guidelines:
- If a field is not mentioned in the notes, use null (not empty string).
- For findings and recommendations, infer category/priority from context.
- Be conservative: only extract what is clearly written.
- Preserve the consultant's intent and phrasing in descriptions.
- If handwriting is illegible, note it in raw_text and use null for that field.

Return ONLY valid JSON, no markdown or explanation.
```

---

## ServiceM8 Integration Details

### Authentication
- **Method**: OAuth2 or API Key (via ServiceM8 dashboard)
- **Scope**: Read/write jobs, clients, custom fields, attachments

### Push Logic
```python
def push_to_servicem8(extracted_data, servicem8_client_id=None, servicem8_job_id=None):
    """
    Push extracted data into ServiceM8.
    If servicem8_client_id is not provided, create new client.
    If servicem8_job_id is not provided, create new job linked to client.
    """
    
    # 1. Create or update client
    client_id = servicem8_client_id or create_client(extracted_data['client_details'])
    
    # 2. Create or update job
    job_id = servicem8_job_id or create_job(client_id, extracted_data['job_details'])
    
    # 3. Append findings + recommendations to job notes
    notes = format_notes(extracted_data['findings'], extracted_data['recommendations'])
    append_to_job_notes(job_id, notes)
    
    # 4. Create tasks from follow-up actions
    for action in extracted_data['follow_up_actions']:
        create_task(job_id, action)
    
    # 5. Upload PDF + structured data summary as attachment
    upload_attachment(job_id, pdf_file, summary_json)
    
    return { job_id, client_id, success: True }
```

---

## UI Mockup (Conceptual)

### Page 1: Upload
```
[Header] Notability to ServiceM8 Agent
[Upload Box] Drag PDF here or click to upload
[Progress] Extracting data from PDF...
```

### Page 2: Review & Approve
```
[Header] Review Extracted Data

[Tabs] Client | Job | Findings | Recommendations | Follow-up

[Tab: Client]
  Name: [editable text field]
  Phone: [editable text field]
  Email: [editable text field]
  Address: [editable text area]

[Tab: Job]
  Location: [editable text field]
  Job Type: [editable text field]
  Estimated Cost: [editable text field]

[Tab: Findings]
  [List of findings with inline edit buttons]
  + Add Finding

[Tab: Recommendations]
  [List of recommendations with priority badges]
  + Add Recommendation

[Tab: Follow-up]
  [List of tasks with due dates]
  + Add Task

[Raw Text View] (expandable)
  Full extracted text for verification

[Actions]
  [Cancel] [Edit & Re-Extract] [Approve & Push to ServiceM8]
```

### Page 3: Push Confirmation
```
[Header] Pushing to ServiceM8...
[Progress Bar]
[Status Log]
  ✓ Client updated (ID: C123456)
  ✓ Job created (ID: J789012)
  ✓ Notes appended
  ✓ Tasks created
  ✓ PDF attached

[Button] View in ServiceM8 | New Consultation
```

---

## Error Handling (MVP Level)

- **Upload fails**: Show user-friendly message, allow retry
- **PDF is corrupt**: Show "Unable to read PDF, please try another file"
- **OpenAI API fails**: Show "Extraction failed, please try again or contact support"
- **ServiceM8 API fails**: Show extracted data + error, allow user to retry push
- **Network timeout**: Basic retry logic (1 retry after 5 seconds)

---

## Testing Strategy (MVP)

- **Unit**: Test extraction prompt + JSON parsing
- **Integration**: Test full workflow end-to-end with sample PDFs
- **Manual**: Consultant uploads real consultation PDF, reviews, approves, verifies in ServiceM8

---

## Deployment Checklist

- [ ] ServiceM8 API key stored in environment
- [ ] OpenAI API key stored in environment
- [ ] Database initialized (schema + migrations)
- [ ] Frontend deployed to Railway or Vercel
- [ ] Backend deployed to Railway
- [ ] HTTPS enabled
- [ ] User can create account and login
- [ ] Sample PDF upload works end-to-end
- [ ] ServiceM8 push is successful

---

## Future Enhancements (Post-MVP)

1. **Specialized OCR models** for handwriting (e.g., Tesseract, Azure Form Recognizer) if OpenAI API costs become prohibitive
2. **Template recognition** — auto-detect PDF template type and optimize extraction accordingly
3. **Native iPad app** — eliminate the export step
4. **Batch processing** — upload multiple PDFs at once
5. **ServiceM8 custom field mapping** — user-configurable mapping of extracted fields to ServiceM8 custom fields
6. **Analytics** — track extraction accuracy, time saved, common issues
7. **Integration with other field service software** (HubSpot, Jobber, etc.)

---

## Success Criteria

1. ✓ Consultant uploads handwritten PDF
2. ✓ Agent extracts 80%+ of data accurately
3. ✓ Consultant reviews + approves in <2 minutes
4. ✓ Data pushes to ServiceM8 correctly
5. ✓ No manual transcription needed
6. ✓ Saves 20+ minutes per consultation for small team
