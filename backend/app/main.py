import logging
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import get_settings
from app.database import get_db, init_db
from app.models import AuditLog, Consultation, User
from app.schemas import (
    ApprovalRequest,
    ConsultationListResponse,
    ConsultationResponse,
    ConsultationUpdateRequest,
    ConsultationUploadResponse,
    GenericResponse,
    LoginRequest,
    ReExtractRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.extraction_service import extract_with_vision_model
from app.services.pdf_service import save_pdf, validate_pdf
from app.services.push_service import push_to_servicem8


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notability_agent")
settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def serialize_consultation(consultation: Consultation) -> ConsultationResponse:
    payload = {
        "id": consultation.id,
        "user_id": consultation.user_id,
        "original_pdf_path": consultation.original_pdf_path,
        "extracted_data": consultation.extracted_data_json,
        "status": consultation.status,
        "error_message": consultation.error_message,
        "created_at": consultation.created_at,
        "updated_at": consultation.updated_at,
    }
    return ConsultationResponse.model_validate(payload)


def audit(db: Session, user_id: int | None, action: str, details: dict | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, details=details or {}))
    db.commit()


def run_extraction(consultation_id: int, feedback: str = "") -> None:
    db = next(get_db())
    try:
        consultation = db.get(Consultation, consultation_id)
        if consultation is None:
            return
        consultation.status = "processing"
        db.commit()
        extracted = extract_with_vision_model(consultation.original_pdf_path, feedback)
        consultation.extracted_data_json = extracted.model_dump()
        consultation.status = "extracted"
        consultation.error_message = None
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive background path
        logger.exception("Extraction failed for consultation %s", consultation_id)
        consultation = db.get(Consultation, consultation_id)
        if consultation:
            consultation.status = "failed"
            consultation.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")
    user = User(email=payload.email.lower(), name=payload.name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    audit(db, user.id, "user_registered")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=UserResponse.model_validate(user))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    audit(db, user.id, "user_logged_in")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=UserResponse.model_validate(user))


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@app.post("/consultations/upload", response_model=ConsultationUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_consultation(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultationUploadResponse:
    contents = await validate_pdf(file)
    saved_path = save_pdf(contents, file.filename)
    consultation = Consultation(user_id=current_user.id, original_pdf_path=str(saved_path), status="pending")
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    audit(db, current_user.id, "consultation_uploaded", {"consultation_id": consultation.id})
    background_tasks.add_task(run_extraction, consultation.id)
    return ConsultationUploadResponse(consultation_id=consultation.id, extraction_status="processing")


@app.get("/consultations", response_model=ConsultationListResponse)
def list_consultations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultationListResponse:
    query = db.query(Consultation).filter(Consultation.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Consultation.created_at.desc()).offset(offset).limit(limit).all()
    return ConsultationListResponse(items=[serialize_consultation(item) for item in items], total=total, limit=limit, offset=offset)


@app.get("/consultations/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultationResponse:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found.")
    return serialize_consultation(consultation)


@app.put("/consultations/{consultation_id}", response_model=ConsultationResponse)
def update_consultation(
    consultation_id: int,
    payload: ConsultationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultationResponse:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found.")
    consultation.extracted_data_json = payload.extracted_data.model_dump()
    consultation.status = "reviewed"
    db.commit()
    db.refresh(consultation)
    audit(db, current_user.id, "consultation_updated", {"consultation_id": consultation.id})
    return serialize_consultation(consultation)


@app.post("/consultations/{consultation_id}/re-extract", response_model=ConsultationUploadResponse)
def re_extract(
    consultation_id: int,
    payload: ReExtractRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultationUploadResponse:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found.")
    consultation.status = "processing"
    db.commit()
    background_tasks.add_task(run_extraction, consultation.id, payload.feedback)
    audit(db, current_user.id, "consultation_reextract_requested", {"consultation_id": consultation.id})
    return ConsultationUploadResponse(consultation_id=consultation.id, extraction_status="processing")


@app.post("/consultations/{consultation_id}/approve")
def approve_consultation(
    consultation_id: int,
    payload: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found.")
    consultation.status = "pushing"
    db.commit()
    try:
        response = push_to_servicem8(db, consultation, payload.servicem8_job_id)
    except Exception as exc:
        consultation.status = "failed"
        consultation.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ServiceM8 push failed: {exc}") from exc
    audit(db, current_user.id, "consultation_pushed", {"consultation_id": consultation.id})
    return {"consultation_id": consultation.id, "status": "pushed", "servicem8_response": response}


@app.delete("/consultations/{consultation_id}", response_model=GenericResponse)
def delete_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericResponse:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None or consultation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found.")
    path = Path(consultation.original_pdf_path)
    db.delete(consultation)
    db.commit()
    if path.exists():
        path.unlink()
    audit(db, current_user.id, "consultation_deleted", {"consultation_id": consultation_id})
    return GenericResponse(message="Consultation deleted.")


@app.get("/config/servicem8")
def servicem8_status() -> dict[str, bool]:
    return {"configured": bool(settings.servicem8_api_key)}
