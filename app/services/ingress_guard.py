"""Resolve Unipile webhook payloads to workflow ingress decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.config import settings
from app.core.logger import get_logger
from app.domain.guards import (
    can_process_email_reply,
    can_start_pdf_assignment,
    find_rate_confirmation_attachment,
)
from app.domain.unipile_webhook import normalize_attachments
from app.integrations.unipile.client import UnipileClient, UnipileError
from app.tools import sheets as sheet_tools

logger = get_logger(__name__)


def _thread_has_crm_row(thread_id: str) -> bool:
    if not thread_id:
        return False
    if settings.FIXTURE_MODE:
        return sheet_tools.read_row_by_thread_id(thread_id) is not None
    if not settings.GOOGLE_SHEET_ID or not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        return False
    try:
        return sheet_tools.read_row_by_thread_id(thread_id) is not None
    except Exception:
        logger.warning("thread lookup failed thread_id=%s", thread_id, exc_info=True)
        return False

Action = Literal["pdf_assignment", "email_reply", "ignore"]


@dataclass
class IngressDecision:
    action: Action
    run_payload: dict[str, Any] | None = None
    skip_reason: str | None = None


def _resolve_attachments(payload: dict[str, Any], *, account_id: str) -> list[Any]:
    attachments = normalize_attachments(payload.get("attachments"))
    if find_rate_confirmation_attachment(attachments):
        return attachments
    if not payload.get("has_attachments"):
        return attachments

    email_id = str(payload.get("email_id") or payload.get("id") or "")
    if not email_id or settings.FIXTURE_MODE or not settings.UNIPILE_API_KEY:
        return attachments

    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    try:
        email = UnipileClient().get_email(email_id, account_id=aid or None)
    except UnipileError:
        logger.warning("fetch email for attachments failed email_id=%s", email_id, exc_info=True)
        return attachments
    fetched = normalize_attachments(email.get("attachments"))
    return fetched or attachments


def resolve_unipile_ingress(payload: dict[str, Any], *, account_id: str) -> IngressDecision:
    email_id = str(payload.get("email_id") or payload.get("id") or "")
    thread_id = str(payload.get("thread_id") or "")
    subject = str(payload.get("subject") or "")
    attachments = _resolve_attachments(payload, account_id=account_id)

    rate_att, _pdf_skip = can_start_pdf_assignment(attachments)
    if rate_att:
        return IngressDecision(
            action="pdf_assignment",
            run_payload={
                "event_type": "pdf_assignment",
                "email_id": email_id,
                "attachment_id": str(rate_att.get("id") or ""),
                "attachment_name": str(rate_att.get("name") or rate_att.get("filename") or ""),
                "thread_id": thread_id,
                "account_id": account_id,
                "subject": subject,
            },
        )

    thread_has_row = _thread_has_crm_row(thread_id)
    reply_skip = can_process_email_reply(
        subject=subject,
        thread_id=thread_id,
        thread_has_crm_row=thread_has_row,
    )
    if reply_skip:
        return IngressDecision(action="ignore", skip_reason=reply_skip)

    return IngressDecision(
        action="email_reply",
        run_payload={
            "event_type": "email_reply",
            "thread_id": thread_id,
            "email_id": email_id,
            "account_id": account_id,
            "subject": subject,
        },
    )
