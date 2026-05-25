# Strategic Implementation Plan: Notability-to-ServiceM8 Agent

## Phase Overview

This plan breaks the Notability-to-ServiceM8 agent into **11 focused implementation steps**, each designed to build on the previous one without orphaned code. The progression moves from backend infrastructure → core extraction logic → API layer → frontend UI → integration → polish.

---

## Implementation Roadmap

### Step 1: Project Boilerplate & Database Schema
**Goal**: Set up the repo structure, FastAPI app, PostgreSQL schema, and basic models.

**Delivers**: A working FastAPI server that can be started locally, connected to PostgreSQL, with all tables initialized.

```
# IMPLEMENTATION PROMPT 1

You are building the backend for a Notability-to-ServiceM8 agent. Start by setting up the project boilerplate.

## Context
- Framework: FastAPI (Python 3.11+)
- Database: PostgreSQL with SQLAlchemy ORM
- Authentication: JWT-based (simple email/password, no OAuth yet)
- Deployment target: Railway.app (but should work locally first)

## Task: Set up project boilerplate with database models

1. Create a FastAPI project structure:
   ```
   notability-agent/
   ├── backend/
   │   ├── main.py (FastAPI app entry point)
   │   ├── config.py (environment variables, database URL)
   │   ├── models.py (SQLAlchemy ORM models)
   │   ├── database.py (session management, engine setup)
   │   ├── schemas.py (Pydantic request/response schemas)
   │   └── requirements.txt
   ├── frontend/
   │   └── (empty for now)
   └── .gitignore
   ```

2. Set up FastAPI main.py:
   - Create a FastAPI() app instance
   - Configure CORS
   - Add a test endpoint: GET /health that returns {"status": "ok"}
   - Set up basic error handling middleware

3. Create database.py:
   - Use SQLAlchemy with PostgreSQL (psycopg2)
   - Define Base for ORM models
   - Create get_db() dependency for FastAPI
   - Create an engine that reads DATABASE_URL from environment

4. Define SQLAlchemy models in models.py:
   - User: id, email, password_hash (bcrypt), name, created_at
   - Consultation: id, user_id (FK), original_pdf_path, extracted_data_json (JSONB), status (enum: pending|approved|pushed|failed), created_at, updated_at
   - ConsultationPush: id, consultation_id (FK), servicem8_job_id, servicem8_client_id, push_timestamp, push_response_json
   - AuditLog: id, user_id (FK), action, details, timestamp

5. Create schemas.py:
   - UserCreate (email, password, name)
   - UserResponse (id, email, name, created_at)
   - ConsultationResponse (id, status, extracted_data, created_at)
   - GenericResponse (success, message)

6. Create requirements.txt with:
   - fastapi==0.104.1
   - sqlalchemy==2.0.23
   - psycopg2-binary==2.9.9
   - pydantic==2.5.0
   - python-dotenv==1.0.0
   - bcrypt==4.1.1
   - PyJWT==2.8.1

7. Create .env.example:
   ```
   DATABASE_URL=postgresql://user:password@localhost/notability_agent
   JWT_SECRET=your-secret-key
   CLAUDE_API_KEY=your-claude-key
   SERVICEM8_API_KEY=your-servicem8-key
   ```

8. Test locally:
   - Create a PostgreSQL database named notability_agent
   - Create alembic migrations to initialize schema (or use SQLAlchemy's create_all)
   - Start the FastAPI server: uvicorn backend.main:app --reload
   - Verify GET /health returns 200 with {"status": "ok"}

Output the complete code for all files. Make sure the database connection is tested and the schema is initialized.
```

---

### Step 2: User Authentication (Register & Login)
**Goal**: Implement JWT-based authentication so users can register and login.

**Delivers**: Working `/auth/register` and `/auth/login` endpoints; JWT tokens issued and validated.

```
# IMPLEMENTATION PROMPT 2

Building on the FastAPI project from Step 1, implement user authentication.

## Context
From Step 1, we have:
- FastAPI app with SQLAlchemy models (User, Consultation, etc.)
- Database connected and working
- JWT_SECRET in environment

## Task: Implement JWT authentication

1. Create a new file: backend/auth.py
   - Implement hash_password(password: str) using bcrypt
   - Implement verify_password(plain: str, hashed: str) using bcrypt
   - Implement create_access_token(data: dict, expires_delta: timedelta = None) that returns a JWT
   - Implement a dependency get_current_user(token: str = Depends(HTTPBearer())) that validates JWT and returns User object
   - Define HTTPException responses for 401/403 errors

2. Update schemas.py to add:
   - TokenResponse (access_token: str, token_type: str)
   - LoginRequest (email: str, password: str)

3. Create backend/routes/auth.py:
   - POST /auth/register: 
     * Request body: UserCreate (email, password, name)
     * Hash password, create User in DB
     * Return UserResponse (id, email, name, created_at)
     * Handle duplicate email error (409 Conflict)
   - POST /auth/login:
     * Request body: LoginRequest (email, password)
     * Find user by email, verify password
     * Create JWT token, return TokenResponse
     * Handle invalid credentials (401 Unauthorized)
   - GET /auth/me:
     * Requires auth (use get_current_user dependency)
     * Return current UserResponse

4. Update main.py:
   - Import and include auth router: app.include_router(auth_router, prefix="/auth", tags=["auth"])
   - Test endpoints using curl or Postman

5. Test the workflow:
   - POST /auth/register with {"email": "test@example.com", "password": "password", "name": "Test User"}
   - Verify user is created in DB
   - POST /auth/login with {"email": "test@example.com", "password": "password"}
   - Extract JWT token from response
   - GET /auth/me with Authorization header: "Bearer <token>"
   - Verify it returns the correct user

Output the complete code for auth.py, updated schemas.py, and updated main.py. Ensure auth is working end-to-end.
```

---

### Step 3: PDF Upload & Storage
**Goal**: Implement PDF file upload with validation and storage.

**Delivers**: Working `/consultations/upload` endpoint that accepts PDF files, validates them, stores locally, and creates a Consultation record.

```
# IMPLEMENTATION PROMPT 3

Building on the authenticated FastAPI app from Steps 1-2, implement PDF upload and storage.

## Context
From previous steps:
- FastAPI app with User authentication working
- SQLAlchemy models including Consultation
- Database connected

## Task: Implement PDF upload and storage

1. Create backend/services/pdf_service.py:
   - Implement validate_pdf(file: UploadFile) -> bool:
     * Check MIME type is application/pdf
     * Check file size <= 10 MB
     * Attempt to open with pypdf to verify it's a valid PDF
     * Return True if valid, raise HTTPException if not
   - Implement save_pdf(file: UploadFile, user_id: int, db: Session) -> Consultation:
     * Use validate_pdf
     * Generate unique filename: f"{user_id}_{uuid4()}_{file.filename}"
     * Save to ./uploads/ directory
     * Create Consultation record in DB with pdf_path, status=pending, empty extracted_data
     * Return created Consultation
   - Implement get_consultation_by_id(consultation_id: int, user_id: int, db: Session) -> Consultation:
     * Query DB, verify ownership (user_id matches)
     * Return Consultation or raise 404

2. Create backend/routes/consultations.py:
   - POST /consultations/upload:
     * Requires auth (get_current_user)
     * Accept File parameter (UploadFile)
     * Call pdf_service.save_pdf()
     * Return ConsultationResponse with consultation_id, status, created_at
     * Handle exceptions gracefully (400 for invalid PDF, 413 for too large)
   - GET /consultations/{id}:
     * Requires auth
     * Verify user owns this consultation
     * Return ConsultationResponse with extracted_data (if available)

3. Update main.py:
   - Import and include consultations router
   - Create ./uploads directory (or ensure it exists)

4. Update requirements.txt to add:
   - pypdf==3.17.1
   - python-multipart==0.0.6
   - pdf2image==1.16.3

5. Test the workflow:
   - Generate a sample PDF file (or use a real consultation note PDF)
   - POST /consultations/upload with the PDF file
   - Verify file is saved to ./uploads/
   - Verify Consultation record is created in DB
   - GET /consultations/{id} to retrieve it
   - Verify status is "pending" and extracted_data is null

Output complete code for pdf_service.py, consultations router, updated main.py, and requirements.txt. Ensure file upload works end-to-end.
```

---

### Step 4: PDF to Images & Claude Extraction Setup
**Goal**: Convert PDF pages to images and implement the extraction logic using Claude Vision API.

**Delivers**: Working extraction that reads a PDF, converts to images, sends to Claude, and returns structured JSON.

```
# IMPLEMENTATION PROMPT 4

Building on the FastAPI app with PDF upload from Steps 1-3, implement PDF-to-image conversion and Claude extraction.

## Context
From previous steps:
- PDF upload working
- Consultation model stores extracted_data as JSONB
- Claude API key available in environment

## Task: Implement PDF extraction using Claude Vision API

1. Create backend/services/extraction_service.py:
   - Implement pdf_to_images(pdf_path: str) -> List[bytes]:
     * Use pdf2image.convert_from_path()
     * Convert each page to JPEG bytes (PIL Image.tobytes())
     * Return list of image bytes (one per page)
   
   - Implement extract_with_claude(images: List[bytes], feedback: str = None) -> dict:
     * Build system prompt (from spec, include guidelines)
     * If feedback is provided, append it to the prompt
     * Construct messages with vision blocks for each image:
       {
         "role": "user",
         "content": [
           {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_image}},
           ...for each image...
           {"type": "text", "text": "Extract structured data..."}
         ]
       }
     * Call Anthropic API (use requests library for now)
     * Parse response JSON (Claude returns structured JSON per spec)
     * Validate JSON schema matches expected structure
     * Return extracted data dict

   - Implement validate_extracted_data(data: dict) -> bool:
     * Check required top-level keys exist: client_details, job_details, findings, recommendations, follow_up_actions, raw_text
     * Return True if valid, else raise ValueError

2. Create backend/schemas/extraction.py:
   - Define ExtractedData Pydantic model matching the JSON schema from spec
   - Include validators for each section

3. Create a background task runner (using Celery or simple threading for MVP):
   - For now, use threading.Thread or FastAPI background_tasks
   - Do NOT block the HTTP response while extraction runs
   - Update Consultation status to "processing"

4. Update backend/routes/consultations.py:
   - POST /consultations/upload now also triggers extraction:
     * After saving PDF, start extraction in background
     * Return ConsultationResponse with extraction_status: "processing"
   - GET /consultations/{id}:
     * Return extracted_data if ready, or extraction_status if still processing

5. Test the workflow:
   - Upload a real handwritten consultation PDF
   - Verify extraction starts in background
   - GET /consultations/{id} multiple times, see status progress
   - Verify extracted_data appears in response once complete
   - Log the actual Claude API response for inspection

Output complete code for extraction_service.py, updated routes, and extraction schema. Ensure end-to-end extraction works (may take a few seconds).
```

---

### Step 5: Review & Approval UI - Backend Support
**Goal**: Add endpoints to support the review/approval workflow (get extracted data, update data, re-extract).

**Delivers**: PUT /consultations/{id}, POST /consultations/{id}/re-extract, and supporting logic.

```
# IMPLEMENTATION PROMPT 5

Building on the extraction service from Steps 1-4, implement backend endpoints for review and approval.

## Context
From previous steps:
- Extraction is working and populating extracted_data
- User authentication in place
- Consultation model has status field

## Task: Add review/approval endpoints

1. Update backend/routes/consultations.py:
   - PUT /consultations/{id}:
     * Requires auth, verify ownership
     * Request body: partial ConsultationData (allow partial updates)
     * Update Consultation.extracted_data in DB
     * Return updated ConsultationResponse
     * Only allow updates if status is "pending"
   
   - POST /consultations/{id}/approve:
     * Requires auth, verify ownership
     * Request body: optional { servicem8_job_id, servicem8_client_id }
     * Change status to "pushing"
     * Trigger push_to_servicem8 in background
     * Return ConsultationResponse with status "pushing"
   
   - POST /consultations/{id}/re-extract:
     * Requires auth, verify ownership
     * Request body: { feedback: str }
     * Only allowed if status is "pending"
     * Re-run extraction_with_claude, passing feedback
     * Update extracted_data with new results
     * Return ConsultationResponse with new extracted_data
   
   - GET /consultations:
     * Requires auth
     * List all consultations for current user (with pagination: limit, offset)
     * Return list of ConsultationResponse objects
   
   - DELETE /consultations/{id}:
     * Requires auth, verify ownership
     * Delete Consultation record
     * Delete associated PDF file
     * Return {"success": true}

2. Update schemas.py:
   - Add ConsultationUpdateRequest (partial model, all fields optional)
   - Add ApprovalRequest (servicem8_job_id, servicem8_client_id both optional)
   - Add ReExtractRequest (feedback: str)
   - Add ConsultationListResponse (list of consultations)

3. Test the workflow:
   - Upload a PDF, let extraction complete
   - GET /consultations/{id} to see extracted_data
   - PUT /consultations/{id} to update a field (e.g., client name)
   - Verify update is reflected in DB
   - POST /consultations/{id}/re-extract with feedback
   - Verify extraction runs again with feedback included
   - GET /consultations to list all consultations

Output complete code for updated routes, schemas, and test scenarios. Ensure review/approval flow works end-to-end (before ServiceM8 push).
```

---

### Step 6: ServiceM8 API Integration
**Goal**: Implement the ServiceM8 client and push logic.

**Delivers**: Working ServiceM8 integration that can create clients, jobs, notes, tasks, and attachments.

```
# IMPLEMENTATION PROMPT 6

Building on the review/approval endpoints from Steps 1-5, implement ServiceM8 API integration.

## Context
From previous steps:
- Extraction and review working
- Consultation can be approved
- Need to push data to ServiceM8

## Task: Implement ServiceM8 client and push logic

1. Create backend/services/servicem8_service.py:
   - Implement ServiceM8Client class:
     * __init__(api_key: str):
       - Store API key from environment
       - Base URL: https://api.servicem8.com/api_1.0/ (adjust based on actual ServiceM8 API)
     * _request(method: str, endpoint: str, data: dict = None) -> dict:
       - Make HTTP request with auth header
       - Handle errors gracefully (retry logic for MVP is simple: 1 retry)
       - Return parsed JSON response
   
   - Implement get_or_create_client(client_details: dict) -> str:
     * client_details has: name, phone, email, address
     * Search for existing client by name/email
     * If exists, return client_id
     * If not, create new client via API
     * Return client_id
   
   - Implement get_or_create_job(client_id: str, job_details: dict) -> str:
     * job_details has: location, job_type, estimated_cost
     * Create new job linked to client_id
     * Return job_id
   
   - Implement append_notes(job_id: str, findings: list, recommendations: list) -> bool:
     * Format findings and recommendations as readable text
     * Append to job notes
     * Return success boolean
   
   - Implement create_tasks(job_id: str, follow_up_actions: list) -> bool:
     * For each follow_up_action in list
     * Create task with description, due_date (if provided)
     * Link to job_id
     * Return success boolean
   
   - Implement upload_attachment(job_id: str, pdf_path: str, summary_json: dict) -> bool:
     * Upload original PDF as attachment
     * Upload summary JSON as text/document attachment
     * Return success boolean

2. Create backend/services/push_service.py:
   - Implement push_to_servicem8(consultation: Consultation, servicem8_job_id: str = None, servicem8_client_id: str = None) -> dict:
     * Load ServiceM8Client with API key from environment
     * Extract extracted_data from consultation
     * Create/get client: client_id = get_or_create_client(extracted_data['client_details'], servicem8_client_id)
     * Create/get job: job_id = get_or_create_job(client_id, extracted_data['job_details'], servicem8_job_id)
     * Append notes: append_notes(job_id, extracted_data['findings'], extracted_data['recommendations'])
     * Create tasks: create_tasks(job_id, extracted_data['follow_up_actions'])
     * Upload attachments: upload_attachment(job_id, consultation.original_pdf_path, extracted_data)
     * Create ConsultationPush record in DB
     * Update Consultation status to "pushed"
     * Return {"success": True, "job_id": job_id, "client_id": client_id}

3. Update backend/routes/consultations.py:
   - POST /consultations/{id}/approve now calls push_to_servicem8 in background
   - Handle push errors: update Consultation status to "failed", store error message
   - Provide user feedback on push success/failure

4. Update requirements.txt:
   - (No new dependencies, using requests which is already available)

5. Test the workflow:
   - Get ServiceM8 API key and test account
   - Upload a PDF, extract, review
   - POST /consultations/{id}/approve
   - Monitor background task, verify push completes
   - Check ServiceM8 account: verify client, job, notes, tasks, attachments created
   - Handle edge cases: invalid credentials, API errors

Output complete code for servicem8_service.py, push_service.py, and updated routes. Ensure ServiceM8 integration works end-to-end.
```

---

### Step 7: React Frontend - Setup & Auth
**Goal**: Create a React TypeScript frontend with authentication UI.

**Delivers**: Working login and register pages, JWT token storage, API client setup.

```
# IMPLEMENTATION PROMPT 7

Create a React TypeScript frontend for the Notability agent. Start with auth UI and API client.

## Context
- Backend is running with auth endpoints working
- Frontend will be served from same domain or CORS-enabled
- Use React 18, TypeScript, Tailwind CSS
- Store JWT in localStorage

## Task: Set up React frontend with auth

1. Create frontend structure using Create React App or Vite:
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── AuthForm.tsx
   │   │   ├── LoginPage.tsx
   │   │   ├── RegisterPage.tsx
   │   ├── services/
   │   │   ├── api.ts (HTTP client + auth logic)
   │   ├── hooks/
   │   │   ├── useAuth.ts
   │   ├── pages/
   │   │   ├── HomePage.tsx
   │   │   ├── ConsultationPage.tsx
   │   ├── App.tsx
   │   ├── App.css (or use Tailwind)
   │   └── index.tsx
   ├── package.json
   ├── tsconfig.json
   └── tailwind.config.js
   ```

2. Create src/services/api.ts:
   - Define API_URL (read from env or hardcode for dev)
   - Implement ApiClient class:
     * get(endpoint: string)
     * post(endpoint: string, data: any)
     * put(endpoint: string, data: any)
     * delete(endpoint: string)
     * All methods handle Authorization header with stored JWT
     * Auto-refresh token if needed, or redirect to login if 401

3. Create src/hooks/useAuth.ts:
   - Implement useAuth hook:
     * Returns: {user, isLoggedIn, login, register, logout}
     * login(email: str, password: str) -> calls POST /auth/login, stores JWT
     * register(email: str, password: str, name: str) -> calls POST /auth/register, logs in
     * logout() -> clears localStorage, redirects to login
     * useEffect to restore session on page load (GET /auth/me)

4. Create login/register components:
   - LoginPage.tsx:
     * Email and password input fields
     * Submit button
     * Link to register page
     * Error handling (show error message on failed login)
   - RegisterPage.tsx:
     * Email, password, name input fields
     * Submit button
     * Link to login page
     * Error handling

5. Create App.tsx with routing:
   - Use React Router v6
   - Route /:
     * If logged in -> HomePage
     * If not logged in -> LoginPage
   - Route /register -> RegisterPage
   - Route /consultation/:id -> ConsultationPage (placeholder for now)

6. Set up Tailwind CSS:
   - Install tailwindcss, postcss, autoprefixer
   - Configure tailwind.config.js
   - Create base CSS with Tailwind directives

7. Test locally:
   - npm install && npm start
   - Navigate to login page
   - Register a new account
   - Verify JWT is stored in localStorage
   - Navigate to home page (should redirect after login)
   - Logout and verify redirect to login

Output complete code for all files above. Ensure auth flow works end-to-end.
```

---

### Step 8: Frontend - PDF Upload & Display
**Goal**: Build the upload form and extracted data review UI.

**Delivers**: A working page to upload PDFs, show extraction status, and display extracted data.

```
# IMPLEMENTATION PROMPT 8

Building on the React auth setup from Step 7, implement the PDF upload and review UI.

## Context
From previous steps:
- React frontend with auth working
- Backend endpoints for upload, extraction, review ready
- Need to show upload UI and extracted data review

## Task: Implement upload and review pages

1. Create src/components/UploadForm.tsx:
   - Drag-and-drop area for PDF upload
   - File input fallback
   - Show file name and size
   - Upload button
   - Show upload progress
   - On upload complete, redirect to review page with consultation_id

2. Create src/components/ExtractionStatus.tsx:
   - Display status: processing, ready, error
   - Show spinner while processing
   - Show error message if extraction failed

3. Create src/pages/UploadPage.tsx:
   - Header: "Upload Consultation Notes"
   - UploadForm component
   - ExtractionStatus component
   - After upload, navigate to /consultation/{id}

4. Create src/components/ReviewForm.tsx:
   - Tabbed interface:
     * Client (name, phone, email, address)
     * Job (location, job_type, estimated_cost)
     * Findings (list of findings with edit buttons)
     * Recommendations (list with priority badges)
     * Follow-up (list of tasks)
   - Show "Raw Text" expandable section
   - Each field is editable (click to edit, click to save)
   - Handle edit/save/cancel
   - Show raw extracted_data JSON for verification

5. Create src/pages/ConsultationPage.tsx:
   - Load consultation data from GET /consultations/{id}
   - Show extraction status
   - If pending, show ReviewForm
   - If approved/pushed/failed, show status + option to re-upload or view details

6. Create src/components/ActionButtons.tsx:
   - Button group: Cancel | Edit & Re-Extract | Approve & Push to ServiceM8
   - Cancel -> delete consultation, return to upload
   - Edit & Re-Extract -> prompt for feedback, call re-extract endpoint, show new data
   - Approve & Push -> call approve endpoint, show progress

7. Update App.tsx routing:
   - Route /upload -> UploadPage
   - Route /consultation/:id -> ConsultationPage
   - After auth, redirect to /upload (home page)

8. Add loading states, error boundaries, and user feedback messages

9. Test locally:
   - Login
   - Upload a PDF
   - Watch extraction progress
   - See extracted data appear
   - Edit a field
   - Try re-extract with feedback
   - Test action buttons

Output complete code for all components and pages. Ensure full upload → extraction → review flow works end-to-end.
```

---

### Step 9: Frontend - ServiceM8 Push Flow
**Goal**: Add UI for approving and pushing data to ServiceM8.

**Delivers**: A push confirmation screen with status updates and success/error handling.

```
# IMPLEMENTATION PROMPT 9

Building on the review UI from Step 8, implement the ServiceM8 push confirmation and status page.

## Context
From previous steps:
- Review and approval flow ready
- Backend push endpoints ready
- Need visual feedback during push and after completion

## Task: Implement ServiceM8 push UI

1. Create src/components/PushConfirmation.tsx:
   - Show a modal/dialog for confirming push
   - Optional fields: servicem8_job_id, servicem8_client_id (allow user to link to existing job/client)
   - Show warning: "This will push data to ServiceM8. Make sure everything is correct."
   - Button: Confirm | Cancel

2. Create src/components/PushProgress.tsx:
   - Display progress bar
   - Show status log with checkmarks:
     * Creating/updating client
     * Creating/updating job
     * Appending notes
     * Creating tasks
     * Uploading attachments
   - Show real-time updates (poll backend every 1 second)

3. Create src/components/PushSuccess.tsx:
   - Show success message
   - Display job_id and client_id returned from backend
   - Button: "View in ServiceM8" (open link)
   - Button: "New Consultation" (return to upload)

4. Create src/components/PushError.tsx:
   - Show error message from backend
   - Show retry button
   - Show option to go back to review and edit

5. Update src/pages/ConsultationPage.tsx:
   - When user clicks "Approve & Push to ServiceM8":
     * Show PushConfirmation modal
     * On confirm, call POST /consultations/{id}/approve
     * Show PushProgress component
     * When push completes, show PushSuccess
     * If push fails, show PushError

6. Add useEffect to poll for push status:
   - GET /consultations/{id} returns updated status
   - Update UI based on status: pushing, pushed, failed
   - Poll every 1-2 seconds until status changes

7. Add error handling:
   - Network errors -> show retry option
   - API errors -> show user-friendly message
   - Timeout -> show timeout message with retry

8. Test locally:
   - Complete upload → review → push flow
   - Watch progress updates in real-time
   - Verify success page appears
   - Verify ServiceM8 data is created
   - Test error scenarios (invalid API key, network failure)

Output complete code for all push-related components. Ensure push flow is smooth and user-friendly.
```

---

### Step 10: Integration Testing & Polish
**Goal**: End-to-end testing, error handling, and refinement.

**Delivers**: A complete working app with proper error handling and user feedback.

```
# IMPLEMENTATION PROMPT 10

Building on the complete app from Steps 1-9, integrate everything and add polish.

## Context
- All backend endpoints ready
- All frontend pages ready
- Need to test end-to-end and fix edge cases

## Task: Integration testing and polish

1. Test end-to-end workflows:
   - Register new user
   - Upload PDF with poor handwriting
   - Edit extracted data
   - Re-extract with feedback
   - Approve and push to ServiceM8
   - Verify data in ServiceM8
   - Upload multiple PDFs for same job
   - Verify merge behavior

2. Error handling:
   - Test with corrupted PDF
   - Test with too-large file
   - Test with invalid credentials (wrong ServiceM8 API key)
   - Test with network timeout
   - Test with missing fields
   - Verify user-friendly error messages appear
   - Verify retry logic works

3. Frontend polish:
   - Add loading spinners
   - Add toast notifications for success/error
   - Add input validation (email format, phone format, etc.)
   - Add confirmation dialogs for destructive actions
   - Ensure responsive design (mobile-friendly)
   - Add accessibility (ARIA labels, keyboard navigation)

4. Backend polish:
   - Add logging for all API calls
   - Add request validation
   - Add rate limiting (simple version: check requests per minute)
   - Add timeouts to external API calls (Claude, ServiceM8)
   - Graceful degradation if Claude fails (show error, allow retry)

5. Performance:
   - Add pagination to consultations list
   - Cache user info after login
   - Avoid re-extracting if extraction already successful
   - Compress images before sending to Claude API

6. Security review:
   - Verify CORS is configured correctly
   - Verify JWT is not exposed in logs
   - Verify file upload sanitizes filenames
   - Verify ServiceM8 API key is not exposed in responses

7. Documentation:
   - Add README with setup instructions
   - Document environment variables
   - Document API endpoints
   - Add example curl commands for testing

8. Test checklist:
   - [ ] User registration works
   - [ ] User login works
   - [ ] PDF upload works with valid PDF
   - [ ] PDF upload rejects invalid files
   - [ ] Extraction runs and completes
   - [ ] Extracted data displays correctly
   - [ ] User can edit fields
   - [ ] Re-extract with feedback works
   - [ ] ServiceM8 push works (with real API key)
   - [ ] Error messages are user-friendly
   - [ ] App works on mobile browser
   - [ ] Logout works

Output the final, polished code with all error handling, validation, and improvements. Run through the full test checklist to ensure everything works.
```

---

### Step 11: Deployment to Railway
**Goal**: Deploy backend and frontend to Railway.app.

**Delivers**: A live app accessible from a public URL.

```
# IMPLEMENTATION PROMPT 11

Deploy the complete Notability-to-ServiceM8 agent to Railway.app.

## Context
- Backend and frontend are complete and tested locally
- Ready to deploy to production
- Need to set up Railway, environment variables, and CI/CD

## Task: Deploy to Railway

1. Prepare backend for deployment:
   - Create Procfile (for Railway):
     web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   - Create runtime.txt:
     python-3.11.5
   - Update requirements.txt (ensure all dependencies are listed)
   - Create .railwayignore to exclude frontend/node_modules

2. Set up Railway PostgreSQL:
   - Create a new Railway project
   - Add PostgreSQL add-on
   - Railway will provide DATABASE_URL automatically
   - Initialize database schema (run alembic migrations on first deploy)

3. Deploy backend to Railway:
   - Create Dockerfile (optional but recommended):
     FROM python:3.11-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install -r requirements.txt
     COPY backend ./backend
     CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
   - Connect GitHub repo to Railway
   - Set environment variables in Railway dashboard:
     * DATABASE_URL (from PostgreSQL add-on)
     * JWT_SECRET (generate a secure random string)
     * CLAUDE_API_KEY
     * SERVICEM8_API_KEY
   - Deploy and verify backend is live (GET /health should return 200)

4. Prepare frontend for deployment:
   - Update API_URL in src/services/api.ts to point to Railway backend URL
   - Build: npm run build
   - Create Procfile for frontend:
     web: npm start (or serve -s build for production)

5. Deploy frontend to Railway (or Vercel):
   - Option A: Deploy to same Railway project (add as separate service)
   - Option B: Deploy to Vercel for simplicity
   - Set environment variables:
     * REACT_APP_API_URL=https://your-railway-backend-url

6. Set up CORS:
   - Backend should allow frontend URL in CORS
   - Update main.py CORS configuration

7. Run migrations:
   - SSH into Railway container (or use railway run command)
   - Run: alembic upgrade head (or SQLAlchemy create_all)

8. Test live:
   - Open frontend URL
   - Register account
   - Upload PDF
   - Verify extraction works
   - Verify ServiceM8 push works with real ServiceM8 account

9. Set up monitoring:
   - Check Railway logs for errors
   - Add basic uptime monitoring
   - Test error scenarios in production

10. Document deployment:
    - Add README section on deployment steps
    - Document how to scale (more workers, more DB)

Output complete Dockerfile, Procfile files, updated config files, and deployment instructions. Verify everything is live and working.
```

---

## Summary

This plan breaks the Notability-to-ServiceM8 agent into 11 focused steps:

1. **Boilerplate**: FastAPI, PostgreSQL, models
2. **Auth**: JWT login/register
3. **PDF Upload**: File storage, validation
4. **Extraction**: Claude Vision API integration
5. **Review**: Endpoints for editing, re-extracting
6. **ServiceM8**: Push logic, client/job creation
7. **Frontend Auth**: React login/register UI
8. **Frontend Upload**: PDF upload form, extraction status
9. **Frontend Push**: ServiceM8 push UI with progress
10. **Polish**: Error handling, validation, testing
11. **Deployment**: Railway deployment

**Total estimated time**: 3–5 days for one developer with the prompts above.

Each step builds on previous work, with no orphaned code. Steps 1–6 are backend; steps 7–9 are frontend; steps 10–11 are integration and deployment.
