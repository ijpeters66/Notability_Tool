from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app


def describe(pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path))
    text_chars = sum(len(page.extract_text() or "") for page in reader.pages)
    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"{pdf_path.name}: {len(reader.pages)} pages, {size_mb:.1f} MB, {text_chars} extracted text chars")


def main() -> None:
    pdfs = sorted(Path("files").glob("*.pdf"))
    for pdf in pdfs:
        describe(pdf)

    sample = Path("files/Anne Donohoe.pdf")
    with TestClient(app) as client:
        email = "client.pdf.check@example.com"
        password = "password123"
        auth_response = client.post("/auth/register", json={"name": "Client PDF Check", "email": email, "password": password})
        if auth_response.status_code == 409:
            auth_response = client.post("/auth/login", json={"email": email, "password": password})
        assert auth_response.status_code in (200, 201), auth_response.text
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}

        with sample.open("rb") as handle:
            upload_response = client.post(
                "/consultations/upload",
                headers=headers,
                files={"file": (sample.name, handle, "application/pdf")},
            )
        assert upload_response.status_code == 201, upload_response.text
        consultation_id = upload_response.json()["consultation_id"]
        detail_response = client.get(f"/consultations/{consultation_id}", headers=headers)
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()
        print(f"Uploaded {sample.name} as consultation {consultation_id} with status {detail['status']}")
        print(f"Raw extracted text chars: {len((detail.get('extracted_data') or {}).get('raw_text') or '')}")


if __name__ == "__main__":
    main()
