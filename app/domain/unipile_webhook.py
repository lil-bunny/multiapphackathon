"""Parse Unipile email webhook HTTP bodies (JSON or form-encoded)."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs

from fastapi import HTTPException, Request

def normalize_attachments(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def normalize_unipile_email_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Coerce Unipile email webhook fields after JSON or form decode."""
    out = dict(payload)
    out["attachments"] = normalize_attachments(out.get("attachments"))
    if out.get("has_attachments") in ("true", "false"):
        out["has_attachments"] = out["has_attachments"] == "true"
    return out


_JSON_FORM_KEYS = frozenset(
    {
        "attachments",
        "from_attendee",
        "to_attendees",
        "cc_attendees",
        "bcc_attendees",
        "reply_to_attendees",
        "in_reply_to",
        "folders",
        "folderIds",
    }
)


def _coerce_form_value(key: str, value: str) -> Any:
    text = value.strip()
    if key in _JSON_FORM_KEYS or text.startswith(("[", "{")):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def normalize_form_payload(form: dict[str, list[str]]) -> dict[str, Any]:
    """Turn ``parse_qs`` output into a flat Unipile-style dict."""
    out: dict[str, Any] = {}
    for key, values in form.items():
        if not values:
            continue
        raw = values[0] if len(values) == 1 else values
        if isinstance(raw, str):
            out[key] = _coerce_form_value(key, raw)
        else:
            out[key] = raw
    return out


def _try_parse_json_object(raw: bytes) -> dict[str, Any] | None:
    if not raw.lstrip().startswith(b"{"):
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def parse_unipile_webhook_body(request: Request) -> dict[str, Any]:
    """Accept Unipile webhooks sent as JSON or url-encoded form fields."""
    raw = await request.body()
    if not raw.strip():
        raise HTTPException(status_code=400, detail="empty webhook body")

    content_type = (request.headers.get("content-type") or "").lower()

    # Unipile often labels JSON bodies as application/x-www-form-urlencoded.
    json_payload = _try_parse_json_object(raw)
    if json_payload is not None:
        return normalize_unipile_email_payload(json_payload)

    if "application/json" in content_type:
        raise HTTPException(status_code=400, detail="invalid json webhook body")

    if "application/x-www-form-urlencoded" in content_type or (
        "multipart/form-data" not in content_type and b"=" in raw
    ):
        decoded = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return normalize_unipile_email_payload(normalize_form_payload(decoded))

    raise HTTPException(
        status_code=400,
        detail=f"unsupported webhook content-type: {content_type or 'unknown'}",
    )
