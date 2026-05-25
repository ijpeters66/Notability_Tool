import httpx

from app.services.extraction_service import extract_with_vision_model


def main() -> None:
    try:
        data = extract_with_vision_model("files/Anne Donohoe.pdf")
    except httpx.HTTPStatusError as exc:
        print(f"Vision API error: {exc.response.status_code}")
        print(exc.response.text[:2000])
        raise SystemExit(1) from exc

    print(
        {
            "client": data.client_details.model_dump(),
            "job": data.job_details.model_dump(),
            "findings": len(data.findings),
            "recommendations": len(data.recommendations),
            "follow_up_actions": len(data.follow_up_actions),
            "visual_notes": len(data.visual_notes),
            "raw_text_chars": len(data.raw_text),
        }
    )


if __name__ == "__main__":
    main()
