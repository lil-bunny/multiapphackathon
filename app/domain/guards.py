"""Pure ingress guard rules for rate confirmation workflow."""

from __future__ import annotations

from typing import Any

RATE_CONFIRMATION_TOKEN = "rate_confirmation"


def normalize_attachment_name(raw: Any) -> str:
    return str(raw or "").strip().lower()


def is_rate_confirmation_attachment(filename: str) -> bool:
    """True for rate_confirmation.pdf, rate_confirmation_2099.pdf, etc."""
    name = normalize_attachment_name(filename)
    return name.startswith(RATE_CONFIRMATION_TOKEN) and name.endswith(".pdf")


def is_rate_confirmation_subject(subject: str) -> bool:
    normalized = str(subject or "").strip().lower().replace(" ", "_")
    return RATE_CONFIRMATION_TOKEN in normalized


def find_rate_confirmation_attachment(attachments: list[Any]) -> dict[str, Any] | None:
    for item in attachments:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("filename") or ""
        if is_rate_confirmation_attachment(str(name)):
            return item
    return None


def can_start_pdf_assignment(attachments: list[Any]) -> tuple[dict[str, Any] | None, str | None]:
    att = find_rate_confirmation_attachment(attachments)
    if att:
        return att, None
    return None, "not_rate_confirmation_pdf"


def can_process_email_reply(
    *,
    subject: str,
    thread_id: str,
    thread_has_crm_row: bool,
) -> str | None:
    """Return skip_reason when reply must not run; None means proceed."""
    if thread_has_crm_row:
        return None
    if is_rate_confirmation_subject(subject):
        return None
    return "not_rate_confirmation_thread"
