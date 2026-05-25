import base64
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx
from pypdf import PdfReader

from app.config import get_settings
from app.schemas import ExtractedData, Finding, FollowUpAction, Recommendation, VisualNote


def pdf_to_images(pdf_path: str) -> list[str]:
    if not shutil.which("pdftoppm"):
        return []
    output_dir = Path(tempfile.mkdtemp(prefix="notability-pages-"))
    output_prefix = output_dir / "page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "120", pdf_path, str(output_prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [str(path) for path in sorted(output_dir.glob("page-*.png"))]


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Vision response did not contain JSON.")
    return json.loads(text[start : end + 1])


def _extract_openai_output_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]

    chunks: list[str] = []
    for item in body.get("output", []):
        for block in item.get("content", []):
            if block.get("type") == "output_text":
                chunks.append(block.get("text", ""))
    return "\n".join(chunk for chunk in chunks if chunk)


def _vision_prompt(feedback: str = "") -> str:
    feedback_block = f"\nUser feedback for this re-extraction: {feedback}\n" if feedback else ""
    return f"""
Read this DDK Dream Doors Kitchens handwritten job sheet and return JSON only.

Capture handwritten content, not just printed form labels. Map the result to this exact schema:
{{
  "client_details": {{
    "name": "client name or null",
    "phone": "phone number or null",
    "email": "email or null",
    "address": "address or null"
  }},
  "job_details": {{
    "location": "job location or null",
    "job_type": "short job type, e.g. kitchen facelift",
    "estimated_cost": "cost estimate or null"
  }},
  "findings": [
    {{ "category": "section/category", "description": "observed or requested work" }}
  ],
  "recommendations": [
    {{ "action": "recommended or requested action", "priority": "high|medium|low", "estimated_effort": "time or null" }}
  ],
  "follow_up_actions": [
    {{ "task": "follow-up task", "due_date": "date or null", "assigned_to": "person or null" }}
  ],
  "visual_notes": [
    {{
      "page": 1,
      "visual_type": "drawing|photo|diagram|other",
      "description": "plain-language summary of the drawing/photo/diagram",
      "relevance": "why it matters for the job, measurements, materials, defects, access, or install planning"
    }}
  ],
  "raw_text": "best-effort full transcription of all handwriting"
}}
{feedback_block}
If a handwritten value is uncertain, keep it in raw_text and use null in structured fields.
Do not ignore sketches, diagrams, or photos. Summarize them in visual_notes, but do not invent exact measurements or product choices unless clearly labelled.
""".strip()


def _extracted_data_json_schema() -> dict:
    nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "client_details": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": nullable_string,
                    "phone": nullable_string,
                    "email": nullable_string,
                    "address": nullable_string,
                },
                "required": ["name", "phone", "email", "address"],
            },
            "job_details": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "location": nullable_string,
                    "job_type": nullable_string,
                    "estimated_cost": {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "null"}]},
                },
                "required": ["location", "job_type", "estimated_cost"],
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["category", "description"],
                },
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "action": {"type": "string"},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "estimated_effort": nullable_string,
                    },
                    "required": ["action", "priority", "estimated_effort"],
                },
            },
            "follow_up_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "task": {"type": "string"},
                        "due_date": nullable_string,
                        "assigned_to": nullable_string,
                    },
                    "required": ["task", "due_date", "assigned_to"],
                },
            },
            "visual_notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "page": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                        "visual_type": {"type": "string", "enum": ["drawing", "photo", "diagram", "other"]},
                        "description": {"type": "string"},
                        "relevance": nullable_string,
                    },
                    "required": ["page", "visual_type", "description", "relevance"],
                },
            },
            "raw_text": {"type": "string"},
        },
        "required": [
            "client_details",
            "job_details",
            "findings",
            "recommendations",
            "follow_up_actions",
            "visual_notes",
            "raw_text",
        ],
    }


def _extract_with_anthropic_vision(pdf_path: str, feedback: str = "") -> ExtractedData:
    settings = get_settings()
    images = pdf_to_images(pdf_path)
    if not images:
        raise RuntimeError("pdftoppm is required for vision extraction but was not found.")

    content: list[dict] = [{"type": "text", "text": _vision_prompt(feedback)}]
    for image_path in images:
        encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": encoded},
            }
        )

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.claude_api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.claude_model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": content}],
        },
        timeout=settings.external_timeout_seconds,
    )
    response.raise_for_status()
    body = response.json()
    response_text = "\n".join(block.get("text", "") for block in body.get("content", []) if block.get("type") == "text")
    return validate_extracted_data(_extract_json(response_text))


def _extract_with_openai_vision(pdf_path: str, feedback: str = "") -> ExtractedData:
    settings = get_settings()
    images = pdf_to_images(pdf_path)
    if not images:
        raise RuntimeError("pdftoppm is required for vision extraction but was not found.")

    content: list[dict] = [{"type": "input_text", "text": _vision_prompt(feedback)}]
    for image_path in images:
        encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{encoded}",
                "detail": "high",
            }
        )

    response = httpx.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key or ''}",
            "content-type": "application/json",
        },
        json={
            "model": settings.openai_model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": 4000,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "notability_extracted_data",
                    "schema": _extracted_data_json_schema(),
                }
            },
        },
        timeout=settings.external_timeout_seconds,
    )
    response.raise_for_status()
    response_text = _extract_openai_output_text(response.json())
    return validate_extracted_data(_extract_json(response_text))


def extract_with_vision_model(pdf_path: str, feedback: str = "") -> ExtractedData:
    settings = get_settings()
    if settings.openai_api_key:
        return _extract_with_openai_vision(pdf_path, feedback)
    if settings.claude_api_key:
        return _extract_with_anthropic_vision(pdf_path, feedback)

    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    source_name = Path(pdf_path).name

    if not text:
        text = (
            f"Uploaded {source_name} with {page_count} page(s). No machine-readable text was found. "
            "Review handwritten notes manually or configure OpenAI vision extraction."
        )
    else:
        text = (
            "OpenAI vision extraction is not configured, so this fallback only captured embedded PDF text. "
            "For handwritten notes, set OPENAI_API_KEY and re-extract.\n\n"
            f"{text}"
        )
    if feedback:
        text = f"{text}\n\nRe-extraction feedback: {feedback}"

    return ExtractedData(
        job_details={"job_type": "DDK job sheet"},
        findings=[Finding(category="Uploaded notes", description=f"{page_count} page PDF received for review.")],
        recommendations=[
            Recommendation(
                action="Configure OpenAI vision extraction and re-extract to capture handwriting.",
                priority="high",
                estimated_effort="2 minutes",
            )
        ],
        follow_up_actions=[FollowUpAction(task="Confirm client and job details before approval.")],
        visual_notes=[
            VisualNote(
                visual_type="other",
                description="PDF may contain handwriting, drawings, diagrams, or photos that require vision extraction.",
                relevance="Keep the original PDF attached to ServiceM8 as the evidence trail.",
            )
        ],
        raw_text=text,
    )


def validate_extracted_data(data: dict) -> ExtractedData:
    return ExtractedData.model_validate(data)
