# Notability-to-ServiceM8 Agent

MVP web app for uploading Notability PDF consultation notes, extracting reviewable structured data, and pushing approved data into ServiceM8.

## Structure

- `backend/` - FastAPI API, SQLAlchemy models, auth, upload, extraction, ServiceM8 push flow.
- `frontend/` - React + TypeScript + Tailwind review UI.
- `files/` - Original project spec, prompt plan, and todo list.

## Backend Setup

```bash
cd backend
python3 -m pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000`. Override with:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Environment Variables

Backend:

- `DATABASE_URL` - PostgreSQL URL for deployment. Defaults to local SQLite.
- `JWT_SECRET` - secret used to sign JWTs.
- `LLM_PROVIDER` - extraction provider: `openai`, `claude`, or `auto`. Defaults to `openai`.
- `OPENAI_API_KEY` - OpenAI API key for vision extraction.
- `OPENAI_MODEL` - OpenAI model for vision extraction. Defaults to `gpt-5-mini`.
- `CLAUDE_API_KEY` - optional legacy Claude Vision extraction key, used only if OpenAI is not configured.
- `CLAUDE_MODEL` - legacy Claude model for vision extraction. Defaults to `claude-3-5-sonnet-latest`.
- `SERVICEM8_API_KEY` - ServiceM8 API key. If absent, push flow returns mock-safe responses.
- `SERVICEM8_BASE_URL` - defaults to `https://api.servicem8.com/api_1.0`.
- `MAX_UPLOAD_BYTES` - defaults to 30 MB for real Notability exports.

Frontend:

- `VITE_API_URL` - backend API URL.

## API Endpoints

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /consultations/upload`
- `GET /consultations`
- `GET /consultations/{id}`
- `PUT /consultations/{id}`
- `POST /consultations/{id}/re-extract`
- `POST /consultations/{id}/approve`
- `DELETE /consultations/{id}`
- `GET /config/servicem8`

## Example API Calls

```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alex","email":"alex@example.com","password":"password123"}'
```

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alex@example.com","password":"password123"}'
```

```bash
curl -X POST http://localhost:8000/consultations/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.pdf"
```

## MVP Notes

The extraction service renders PDF pages with `pdftoppm` and uses OpenAI vision extraction when `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set. Set `LLM_PROVIDER=claude` to use the legacy Claude path, or `LLM_PROVIDER=auto` to try OpenAI first and then Claude. Without a configured provider key, it falls back to `pypdf` text extraction and clearly flags that handwriting has not been captured. The first client sample is about 21 MB, so the default upload limit is 30 MB rather than the original 10 MB planning value.

Drawings, diagrams, and photos are captured as `visual_notes` during vision extraction. They are summarized separately from text fields, and the original PDF should still be pushed as a ServiceM8 attachment as the source of truth.

The default OpenAI model is `gpt-5-mini` because it supports image input and structured outputs while staying cost-conscious for a well-defined extraction workflow.
