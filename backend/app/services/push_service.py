from sqlalchemy.orm import Session

from app.models import Consultation, ConsultationPush
from app.services.servicem8_service import ServiceM8Client


def push_to_servicem8(db: Session, consultation: Consultation, servicem8_job_id: str | None = None) -> dict:
    if not consultation.extracted_data_json:
        raise ValueError("No extracted data is available to push.")

    data = consultation.extracted_data_json
    client = ServiceM8Client()
    client_response = client.get_or_create_client(data.get("client_details", {}))
    client_id = client_response.get("uuid") or client_response.get("id") or "unknown-client"

    job_response = client.get_or_create_job(client_id, data.get("job_details", {}), servicem8_job_id)
    job_id = job_response.get("uuid") or job_response.get("id") or servicem8_job_id or "unknown-job"

    notes_response = client.append_notes(job_id, data.get("raw_text", ""))
    task_responses = client.create_tasks(job_id, data.get("follow_up_actions", []))
    attachment_response = client.upload_attachment(job_id, consultation.original_pdf_path)

    response = {
        "client": client_response,
        "job": job_response,
        "notes": notes_response,
        "tasks": task_responses,
        "attachment": attachment_response,
    }
    db.add(
        ConsultationPush(
            consultation_id=consultation.id,
            servicem8_job_id=job_id,
            servicem8_client_id=client_id,
            push_response_json=response,
        )
    )
    consultation.status = "pushed"
    consultation.error_message = None
    db.commit()
    db.refresh(consultation)
    return response
