# Implementation Checklist: Notability-to-ServiceM8 Agent

## Progress Update - Codex Pass

- [x] Created backend FastAPI project structure under `backend/app`
- [x] Added SQLAlchemy database setup with PostgreSQL support and SQLite local fallback
- [x] Added User, Consultation, ConsultationPush, and AuditLog models
- [x] Added Pydantic schemas for auth, consultation responses, extracted data, updates, approvals, and re-extraction
- [x] Added JWT auth endpoints: register, login, and current user
- [x] Added PDF upload validation, local storage, consultation creation, and background extraction trigger
- [x] Added consultation get/list/update/delete/re-extract/approve endpoints
- [x] Added MVP extraction service with `pypdf` text extraction and placeholder structured data for handwritten PDFs
- [x] Added ServiceM8 client and push service with mock-safe behavior when no API key is configured
- [x] Added React/Vite frontend scaffold with auth, upload, review/edit, re-extract, approve/push, success, and error states
- [x] Added deployment/docs files: README, `.env.example`, Dockerfile, Procfile, runtime
- [x] Tested the real client PDFs in `files/`: blank DDK sheet and filled Anne Donohoe sample
- [x] Raised default upload limit to 30 MB to accept the 20.5 MB Notability test PDF
- [x] Added PDF rendering plus vision extraction path for handwritten job sheets
- [x] Added `visual_notes` for drawings, diagrams, and photos so they are reviewable separately from text findings
- [x] Created `backend/.env` and confirmed legacy Claude and ServiceM8 tokens are detected locally
- [x] Started OpenAI migration: added `OPENAI_API_KEY` / `OPENAI_MODEL`, OpenAI Responses API vision path, provider-neutral extraction function, and OpenAI fallback copy
- [ ] Add a real `OPENAI_API_KEY`, re-extract `Anne Donohoe.pdf`, and review structured handwriting output
- [ ] Verify OpenAI PDF-to-image extraction with a real API key
- [ ] Decide whether to fully remove the legacy Claude fallback after OpenAI extraction is verified
- [ ] Confirm ServiceM8 endpoint payloads against a live ServiceM8 account
- [ ] Run full browser QA after frontend dependencies are installed
- [ ] Deploy and verify Railway/Vercel production flow

## Phase 1: Backend Infrastructure

### Step 1: Project Boilerplate & Database Schema
- [ ] Create FastAPI project structure (main.py, config.py, models.py, database.py, schemas.py)
- [ ] Set up PostgreSQL database connection with SQLAlchemy
- [ ] Create User model (id, email, password_hash, name, created_at)
- [ ] Create Consultation model (id, user_id, original_pdf_path, extracted_data_json, status, created_at, updated_at)
- [ ] Create ConsultationPush model (id, consultation_id, servicem8_job_id, servicem8_client_id, push_timestamp, push_response_json)
- [ ] Create AuditLog model (id, user_id, action, details, timestamp)
- [ ] Create Pydantic schemas (UserCreate, UserResponse, ConsultationResponse, GenericResponse)
- [ ] Create requirements.txt with all dependencies
- [ ] Test FastAPI server starts locally
- [ ] Test GET /health endpoint returns 200
- [ ] Initialize database schema (create tables)

### Step 2: User Authentication
- [ ] Create auth.py with password hashing (bcrypt)
- [ ] Implement create_access_token() JWT generation
- [ ] Implement get_current_user() dependency for protected routes
- [ ] Create POST /auth/register endpoint
- [ ] Create POST /auth/login endpoint
- [ ] Create GET /auth/me endpoint (requires auth)
- [ ] Update schemas.py with TokenResponse, LoginRequest
- [ ] Test registration flow (create user, verify in DB)
- [ ] Test login flow (get JWT token)
- [ ] Test protected endpoint (verify JWT validation)
- [ ] Test error handling (duplicate email, wrong password, invalid token)

### Step 3: PDF Upload & Storage
- [ ] Create pdf_service.py with validate_pdf() and save_pdf()
- [ ] Create uploads/ directory
- [ ] Implement file size validation (max 10 MB)
- [ ] Implement MIME type validation (application/pdf)
- [ ] Implement PDF validity check (pypdf)
- [ ] Create POST /consultations/upload endpoint
- [ ] Create GET /consultations/{id} endpoint
- [ ] Update requirements.txt with pypdf and python-multipart
- [ ] Test file upload with valid PDF
- [ ] Test file upload with invalid file (reject with error)
- [ ] Test file upload with too-large file (reject with error)
- [ ] Verify file is saved to ./uploads/
- [ ] Verify Consultation record is created in DB

### Step 4: PDF to Images & OpenAI Extraction
- [ ] Create extraction_service.py with pdf_to_images()
- [x] Implement provider-neutral extraction using OpenAI vision when `OPENAI_API_KEY` is configured
- [ ] Implement validate_extracted_data() schema validation
- [ ] Create extraction schemas (ExtractedData Pydantic model)
- [ ] Implement background task runner for extraction (threading or async)
- [ ] Update POST /consultations/upload to trigger extraction
- [ ] Update GET /consultations/{id} to return extraction status
- [ ] Test PDF-to-image conversion
- [ ] Test OpenAI API call with sample PDF
- [ ] Test extracted JSON validation
- [ ] Test background extraction completes successfully
- [ ] Test extracted_data appears in GET response
- [ ] Test extraction with poor handwriting (verify graceful handling)

### Step 5: Review & Approval Endpoints
- [ ] Create PUT /consultations/{id} for updating extracted data
- [ ] Create POST /consultations/{id}/re-extract for re-running with feedback
- [ ] Create POST /consultations/{id}/approve for pushing to ServiceM8
- [ ] Create GET /consultations for listing (with pagination)
- [ ] Create DELETE /consultations/{id} for cleanup
- [ ] Update schemas.py with ConsultationUpdateRequest, ApprovalRequest, ReExtractRequest
- [ ] Test PUT endpoint (edit a field, verify in DB)
- [ ] Test re-extract with feedback (verify feedback is passed to OpenAI)
- [ ] Test status transitions (pending → approved → pushing → pushed)
- [ ] Test GET /consultations list endpoint with pagination
- [ ] Test DELETE endpoint (verify file and record are deleted)

### Step 6: ServiceM8 Integration
- [ ] Create servicem8_service.py with ServiceM8Client class
- [ ] Implement _request() method for HTTP calls to ServiceM8 API
- [ ] Implement get_or_create_client()
- [ ] Implement get_or_create_job()
- [ ] Implement append_notes()
- [ ] Implement create_tasks()
- [ ] Implement upload_attachment()
- [ ] Create push_service.py with push_to_servicem8()
- [ ] Update POST /consultations/{id}/approve to call push_to_servicem8()
- [ ] Create ConsultationPush records on successful push
- [ ] Update Consultation status to "pushed" or "failed"
- [ ] Test ServiceM8 API connectivity (verify API key works)
- [ ] Test full push flow: extract → approve → push
- [ ] Test client creation in ServiceM8
- [ ] Test job creation in ServiceM8
- [ ] Test notes append in ServiceM8
- [ ] Test task creation in ServiceM8
- [ ] Test attachment upload in ServiceM8
- [ ] Test error handling (invalid API key, network timeout)

---

## Phase 2: Frontend

### Step 7: React Setup & Authentication
- [ ] Create React project structure (src/components, src/services, src/hooks, src/pages)
- [ ] Create src/services/api.ts with ApiClient class
- [ ] Implement get(), post(), put(), delete() methods
- [ ] Implement JWT token storage (localStorage)
- [ ] Implement Authorization header injection
- [ ] Create src/hooks/useAuth.ts with login(), register(), logout()
- [ ] Create src/components/LoginPage.tsx
- [ ] Create src/components/RegisterPage.tsx
- [ ] Create App.tsx with React Router v6
- [ ] Set up Tailwind CSS
- [ ] Test registration page (create user)
- [ ] Test login page (get JWT token)
- [ ] Test JWT is stored in localStorage
- [ ] Test navigation to home page after login
- [ ] Test logout clears JWT

### Step 8: PDF Upload & Review
- [ ] Create UploadForm.tsx with drag-and-drop
- [ ] Create ExtractionStatus.tsx with spinner and error handling
- [ ] Create UploadPage.tsx
- [ ] Create ReviewForm.tsx with tabbed interface (Client, Job, Findings, Recommendations, Follow-up)
- [ ] Implement inline editing for each field
- [ ] Create ConsultationPage.tsx
- [ ] Create ActionButtons.tsx (Cancel, Edit & Re-Extract, Approve & Push)
- [ ] Update App.tsx routing (/upload, /consultation/:id)
- [ ] Add loading states and error boundaries
- [ ] Test file upload (drag-and-drop and click)
- [ ] Test extraction status polling
- [ ] Test extracted data displays correctly
- [ ] Test field editing (click, edit, save)
- [ ] Test re-extract with feedback
- [ ] Test response to editing in real-time

### Step 9: ServiceM8 Push Flow
- [ ] Create PushConfirmation.tsx modal
- [ ] Create PushProgress.tsx with status log
- [ ] Create PushSuccess.tsx with success message
- [ ] Create PushError.tsx with error message and retry
- [ ] Update ConsultationPage.tsx to show push flow
- [ ] Implement polling for push status (GET /consultations/{id})
- [ ] Test approval flow (click "Approve & Push")
- [ ] Test PushConfirmation modal appears
- [ ] Test PushProgress shows real-time updates
- [ ] Test PushSuccess appears after push completes
- [ ] Test "View in ServiceM8" link works
- [ ] Test error handling (show PushError on failure)
- [ ] Test retry logic for failed push

---

## Phase 3: Integration & Deployment

### Step 10: Polish & Testing
- [ ] Test full end-to-end workflow (register → upload → extract → review → push)
- [ ] Test with multiple PDFs for same job (merge behavior)
- [ ] Test error scenarios:
  - [ ] Corrupted PDF (rejection with error message)
  - [ ] Too-large file (rejection with error message)
  - [ ] Invalid ServiceM8 API key (error on push)
  - [ ] Network timeout (retry logic triggers)
  - [ ] Poor handwriting (extraction still works, user can edit)
- [ ] Frontend polish:
  - [ ] Add loading spinners
  - [ ] Add toast notifications for success/error
  - [ ] Add input validation (email, phone format)
  - [ ] Add confirmation dialogs for destructive actions
  - [ ] Test responsive design (mobile, tablet, desktop)
  - [ ] Test accessibility (keyboard navigation, screen readers)
- [ ] Backend polish:
  - [ ] Add logging to all API calls
  - [ ] Add request validation
  - [ ] Add rate limiting (basic version)
  - [ ] Add timeouts to external API calls
  - [ ] Graceful error messages
- [ ] Performance:
  - [ ] Test pagination on consultations list
  - [ ] Test image compression before OpenAI API
  - [ ] Verify no unnecessary re-extractions
- [ ] Security review:
  - [ ] Verify CORS is configured
  - [ ] Verify JWT is not exposed in logs
  - [ ] Verify file upload sanitizes filenames
  - [ ] Verify ServiceM8 API key is not exposed
- [ ] Documentation:
  - [ ] Write README with setup instructions
  - [ ] Document environment variables
  - [ ] Document API endpoints
  - [ ] Add example curl commands

### Step 11: Deployment to Railway
- [ ] Create Dockerfile for backend
- [ ] Create Procfile for backend
- [ ] Create runtime.txt for backend (Python 3.11.5)
- [ ] Update requirements.txt (verify all dependencies)
- [ ] Set up Railway project
- [ ] Set up Railway PostgreSQL add-on
- [ ] Deploy backend to Railway
- [ ] Set environment variables in Railway:
  - [ ] DATABASE_URL
  - [ ] JWT_SECRET
  - [ ] OPENAI_API_KEY
  - [ ] SERVICEM8_API_KEY
- [ ] Run database migrations on deployed backend
- [ ] Test GET /health on live backend (returns 200)
- [ ] Update frontend API_URL to point to live backend
- [ ] Build frontend (npm run build)
- [ ] Deploy frontend to Vercel or Railway
- [ ] Set environment variables for frontend:
  - [ ] REACT_APP_API_URL
- [ ] Test full flow on live deployment:
  - [ ] Register account
  - [ ] Upload PDF
  - [ ] Verify extraction works
  - [ ] Verify push to ServiceM8 works
- [ ] Set up monitoring (check logs for errors)
- [ ] Test error scenarios in production

---

## Final Verification

- [ ] All 11 implementation steps completed
- [ ] All backend endpoints tested
- [ ] All frontend pages tested
- [ ] Full end-to-end workflow works
- [ ] ServiceM8 data appears correctly
- [ ] Error handling is user-friendly
- [ ] App is responsive (mobile, tablet, desktop)
- [ ] App is accessible (keyboard, screen readers)
- [ ] Performance is acceptable (no slow uploads/extractions)
- [ ] Security review passed
- [ ] Documentation is complete
- [ ] Live deployment is stable

---

## Notes

- **Total Estimated Time**: 3–5 days for one developer
- **Dependencies**: FastAPI, PostgreSQL, OpenAI API, ServiceM8 API, React, Tailwind CSS
- **Deployment**: Railway.app (backend) + Vercel (frontend)
- **MVP Focus**: Functional features first; polish and optimization are secondary

---

## Troubleshooting

If you get stuck on any step:
1. Review the corresponding implementation prompt in `prompt_plan.md`
2. Check the backend/frontend logs for error messages
3. Verify environment variables are set correctly
4. Test API endpoints individually using curl or Postman
5. Use browser DevTools (Network tab) to debug frontend issues
