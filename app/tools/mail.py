"""Mail tools — plain args, delegate to Unipile or fixture store."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.logger import get_logger
from app.domain.mail_attendees import reply_all_cc, reply_all_cc_from_emails
from app.integrations.unipile.client import UnipileClient, UnipileError
from app.services.fixture_store import get_fixture_store
from app.tools.reply_parse import format_thread_for_llm

logger = get_logger(__name__)


def reply_subject(subject: str, shipment_id: str) -> str:
    base = str(subject or "").strip()
    if base.lower().startswith("re:"):
        return base
    if base:
        return f"Re: {base}"
    return f"Re: rate_confirmation {shipment_id}"


def _connected_account_emails() -> set[str]:
    email = str(settings.UNIPILE_ACCOUNT_EMAIL or "").strip().lower()
    return {email} if email else set()


def _resolve_reply_cc(
    *,
    reply_to_email_id: str | None,
    primary_to: str,
    account_id: str | None,
    thread_id: str | None = None,
) -> list[dict[str, str]]:
    if not reply_to_email_id or settings.FIXTURE_MODE or not settings.UNIPILE_API_KEY:
        return []
    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    exclude = _connected_account_emails()
    client = UnipileClient()
    tid = str(thread_id or "").strip()
    if tid:
        try:
            thread_emails = client.list_emails(account_id=aid, thread_id=tid)
            if thread_emails:
                cc = reply_all_cc_from_emails(
                    thread_emails,
                    primary_to=primary_to,
                    exclude_emails=exclude,
                )
                logger.info(
                    "reply cc resolved from thread thread_id=%s cc_count=%s",
                    tid,
                    len(cc),
                )
                return cc
        except UnipileError:
            logger.warning(
                "thread cc lookup failed thread_id=%s; falling back to single email",
                tid,
                exc_info=True,
            )
    try:
        email = client.get_email(reply_to_email_id, account_id=aid or None)
    except UnipileError:
        return []
    return reply_all_cc(
        email,
        primary_to=primary_to,
        exclude_emails=exclude,
    )


def fetch_thread_messages(
    *,
    thread_id: str,
    account_id: str | None = None,
    fixture_messages: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if fixture_messages is not None:
        return fixture_messages
    if settings.FIXTURE_MODE:
        return []
    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    client = UnipileClient()
    emails = client.list_emails(account_id=aid, thread_id=thread_id)
    messages: list[dict[str, Any]] = []
    for email in emails:
        body = email.get("body_plain") or email.get("body") or ""
        from_addr = email.get("from_attendee") or email.get("from") or {}
        if isinstance(from_addr, dict):
            sender = from_addr.get("identifier") or from_addr.get("display_name") or ""
        else:
            sender = str(from_addr)
        messages.append(
            {
                "from": sender,
                "subject": email.get("subject") or "",
                "body": body,
                "body_plain": body,
            }
        )
    return messages


def fetch_pdf_attachment_bytes(
    *,
    email_id: str,
    attachment_id: str,
    account_id: str | None = None,
    fixture_bytes: bytes | None = None,
) -> bytes:
    if fixture_bytes is not None:
        return fixture_bytes
    if settings.FIXTURE_MODE:
        return b""
    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    return UnipileClient().get_email_attachment(email_id, attachment_id, account_id=aid)


def _normalize_email(value: str) -> str:
    return str(value or "").strip()


def send_customer_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    attachment_name: str | None = None,
    attachment_bytes: bytes | None = None,
    account_id: str | None = None,
) -> dict[str, Any]:
    to_email = _normalize_email(to_email)
    if not to_email or "@" not in to_email:
        return {"success": False, "error": "invalid customer email"}

    if settings.FIXTURE_MODE:
        store = get_fixture_store()
        store.sent_emails.append(
            {
                "email_type": "customer",
                "to": to_email,
                "subject": subject,
                "body": body,
                "attachment_name": attachment_name,
            }
        )
        return {"success": True, "fixture": True}

    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    attachments = []
    if attachment_name and attachment_bytes:
        attachments.append((attachment_name, attachment_bytes, "application/pdf"))
    try:
        return UnipileClient().send_email(
            account_id=aid,
            to=[{"display_name": to_email, "identifier": to_email}],
            subject=subject,
            body=body,
            attachments=attachments,
        )
    except UnipileError as exc:
        return {"success": False, "error": str(exc)}


def send_thread_reply(
    *,
    to_email: str,
    subject: str,
    body: str,
    reply_to_email_id: str | None = None,
    account_id: str | None = None,
    thread_id: str | None = None,
    email_type: str = "thread_reply",
    cc: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    cc_list = cc if cc is not None else _resolve_reply_cc(
        reply_to_email_id=reply_to_email_id,
        primary_to=to_email,
        account_id=account_id,
        thread_id=thread_id,
    )
    if settings.FIXTURE_MODE:
        store = get_fixture_store()
        store.sent_emails.append(
            {
                "email_type": email_type,
                "to": to_email,
                "cc": [c.get("identifier") for c in cc_list],
                "subject": subject,
                "body": body,
                "reply_to_email_id": reply_to_email_id,
            }
        )
        return {"success": True, "fixture": True}

    aid = account_id or settings.UNIPILE_ACCOUNT_ID
    try:
        return UnipileClient().send_email(
            account_id=aid,
            to=[{"display_name": to_email, "identifier": to_email}],
            cc=cc_list,
            subject=subject,
            body=body,
            reply_to=reply_to_email_id,
        )
    except UnipileError as exc:
        return {"success": False, "error": str(exc)}


def send_carrier_thread_reply(
    *,
    to_email: str,
    subject: str,
    body: str,
    reply_to_email_id: str | None = None,
    account_id: str | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    return send_thread_reply(
        to_email=to_email,
        subject=subject,
        body=body,
        reply_to_email_id=reply_to_email_id,
        account_id=account_id,
        thread_id=thread_id,
        email_type="carrier_ack",
    )


def carrier_email_from_thread_messages(messages: list[dict[str, Any]]) -> str | None:
    for msg in reversed(messages):
        sender = str(msg.get("from") or "").strip()
        if sender and "@" in sender:
            return sender
    return None


def thread_text_for_llm(messages: list[dict[str, Any]]) -> str:
    return format_thread_for_llm(messages)
