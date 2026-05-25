from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GenericResponse(BaseModel):
    message: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ClientDetails(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class JobDetails(BaseModel):
    location: str | None = None
    job_type: str | None = None
    estimated_cost: str | float | None = None


class Finding(BaseModel):
    category: str
    description: str


class Recommendation(BaseModel):
    action: str
    priority: Literal["high", "medium", "low"] = "medium"
    estimated_effort: str | None = None


class FollowUpAction(BaseModel):
    task: str
    due_date: str | None = None
    assigned_to: str | None = None


class VisualNote(BaseModel):
    page: int | None = None
    visual_type: Literal["drawing", "photo", "diagram", "other"] = "other"
    description: str
    relevance: str | None = None


class ExtractedData(BaseModel):
    client_details: ClientDetails = Field(default_factory=ClientDetails)
    job_details: JobDetails = Field(default_factory=JobDetails)
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    follow_up_actions: list[FollowUpAction] = Field(default_factory=list)
    visual_notes: list[VisualNote] = Field(default_factory=list)
    raw_text: str = ""


class ConsultationResponse(BaseModel):
    id: int
    user_id: int
    original_pdf_path: str
    extracted_data: ExtractedData | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationListResponse(BaseModel):
    items: list[ConsultationResponse]
    total: int
    limit: int
    offset: int


class ConsultationUploadResponse(BaseModel):
    consultation_id: int
    extraction_status: str


class ConsultationUpdateRequest(BaseModel):
    extracted_data: ExtractedData


class ApprovalRequest(BaseModel):
    servicem8_job_id: str | None = None


class ReExtractRequest(BaseModel):
    feedback: str = Field(default="", max_length=2000)
