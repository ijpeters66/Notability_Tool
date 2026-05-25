from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app


def main() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text

        email = "alex.smoke@example.com"
        password = "password123"
        registered = client.post("/auth/register", json={"name": "Alex", "email": email, "password": password})
        if registered.status_code == 409:
            registered = client.post("/auth/login", json={"email": email, "password": password})
        assert registered.status_code in (200, 201), registered.text
        token = registered.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200, me.text

        sample_path = Path("sample-smoke.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with sample_path.open("wb") as handle:
            writer.write(handle)

        with sample_path.open("rb") as handle:
            uploaded = client.post(
                "/consultations/upload",
                headers=headers,
                files={"file": ("sample-smoke.pdf", handle, "application/pdf")},
            )
        assert uploaded.status_code == 201, uploaded.text
        consultation_id = uploaded.json()["consultation_id"]

        detail = client.get(f"/consultations/{consultation_id}", headers=headers)
        assert detail.status_code == 200, detail.text

        listed = client.get("/consultations", headers=headers)
        assert listed.status_code == 200, listed.text

        sample_path.unlink(missing_ok=True)
    print("backend smoke ok")


if __name__ == "__main__":
    main()
