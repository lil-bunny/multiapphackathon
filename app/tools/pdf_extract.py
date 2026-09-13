"""Extract shipment fields from carrier assignment PDF."""

from __future__ import annotations

import re
from typing import Any

import pymupdf

from app.tools.llm import LLMError, chat_json

PDF_EXTRACT_PROMPT = """Extract shipment_id and delivery_date from a carrier assignment document.
Return JSON: {"shipment_id": str, "delivery_date": str ISO-like datetime or date}."""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def shipment_id_from_attachment_name(filename: str) -> str:
    name = str(filename or "").strip().lower()
    match = re.search(r"rate_confirmation[_-]?(\d+)\.pdf$", name)
    if match:
        return f"SHP-{match.group(1)}"
    return ""


def extract_assignment_from_text(text: str) -> dict[str, str]:
    shipment_match = re.search(r"(SHP[-\s]?\d+)", text, re.IGNORECASE)
    date_match = re.search(
        r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?|\d{1,2}/\d{1,2}/\d{4})",
        text,
    )
    shipment_id = shipment_match.group(1).replace(" ", "-").upper() if shipment_match else ""
    delivery_date = date_match.group(1) if date_match else ""
    return {"shipment_id": shipment_id, "delivery_date": delivery_date}


def extract_assignment_from_pdf(
    pdf_bytes: bytes,
    *,
    fixture_result: dict[str, Any] | None = None,
) -> dict[str, str]:
    if fixture_result:
        return {
            "shipment_id": str(fixture_result.get("shipment_id") or ""),
            "delivery_date": str(fixture_result.get("delivery_date") or ""),
        }
    text = extract_text_from_pdf(pdf_bytes)
    heuristic = extract_assignment_from_text(text)
    if heuristic.get("shipment_id") and heuristic.get("delivery_date"):
        return heuristic
    try:
        llm = chat_json(PDF_EXTRACT_PROMPT, text[:8000])
        return {
            "shipment_id": str(llm.get("shipment_id") or ""),
            "delivery_date": str(llm.get("delivery_date") or ""),
        }
    except LLMError:
        return heuristic
