from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings


class ServiceM8Client:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        if not self.settings.servicem8_api_key:
            raise RuntimeError("SERVICEM8_API_KEY is not configured.")
        return {"Authorization": f"Bearer {self.settings.servicem8_api_key}", "Accept": "application/json"}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(base_url=self.settings.servicem8_base_url, timeout=self.settings.external_timeout_seconds) as client:
            response = client.request(method, path, headers=self._headers(), **kwargs)
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()

    def get_or_create_client(self, client_details: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.servicem8_api_key:
            return {"uuid": "mock-client", "mock": True, "client_details": client_details}
        return self._request("POST", "/company.json", json=client_details)

    def get_or_create_job(self, client_id: str, job_details: dict[str, Any], job_id: str | None = None) -> dict[str, Any]:
        if not self.settings.servicem8_api_key:
            return {"uuid": job_id or "mock-job", "mock": True, "client_id": client_id, "job_details": job_details}
        if job_id:
            return {"uuid": job_id}
        payload = {"company_uuid": client_id, **job_details}
        return self._request("POST", "/job.json", json=payload)

    def append_notes(self, job_id: str, notes: str) -> dict[str, Any]:
        if not self.settings.servicem8_api_key:
            return {"job_id": job_id, "mock": True, "notes": notes}
        return self._request("POST", "/jobnote.json", json={"job_uuid": job_id, "note": notes})

    def create_tasks(self, job_id: str, follow_up_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.settings.servicem8_api_key:
            return [{"job_id": job_id, "mock": True, **action} for action in follow_up_actions]
        return [
            self._request("POST", "/task.json", json={"job_uuid": job_id, "description": action.get("task"), **action})
            for action in follow_up_actions
        ]

    def upload_attachment(self, job_id: str, pdf_path: str) -> dict[str, Any]:
        if not self.settings.servicem8_api_key:
            return {"job_id": job_id, "mock": True, "filename": Path(pdf_path).name}
        with Path(pdf_path).open("rb") as handle:
            return self._request("POST", "/attachment.json", files={"file": handle}, data={"job_uuid": job_id})
