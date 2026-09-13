"""Pure helpers for Unipile attendee lists on send/reply."""

from __future__ import annotations

from typing import Any


def attendee_identifier(attendee: Any) -> str:
    if not isinstance(attendee, dict):
        return ""
    return str(attendee.get("identifier") or "").strip().lower()


def _attendee_dict(attendee: Any) -> dict[str, str] | None:
    ident = attendee_identifier(attendee)
    if not ident or "@" not in ident:
        return None
    display = str(attendee.get("display_name") or ident).strip() or ident
    return {"display_name": display, "identifier": ident}


def reply_all_cc_from_emails(
    emails: list[dict[str, Any]],
    *,
    primary_to: str,
    exclude_emails: set[str] | None = None,
) -> list[dict[str, str]]:
    """Merge Reply All CC from every message in a thread."""
    exclude = {primary_to.strip().lower()}
    if exclude_emails:
        exclude.update(e.lower() for e in exclude_emails if e)
    cc: list[dict[str, str]] = []
    seen: set[str] = set()
    for email in emails:
        for key in ("to_attendees", "cc_attendees"):
            raw = email.get(key)
            if not isinstance(raw, list):
                continue
            for attendee in raw:
                parsed = _attendee_dict(attendee)
                if not parsed or parsed["identifier"] in exclude or parsed["identifier"] in seen:
                    continue
                seen.add(parsed["identifier"])
                cc.append(parsed)
        from_attendee = _attendee_dict(email.get("from_attendee"))
        if from_attendee and from_attendee["identifier"] not in exclude and from_attendee["identifier"] not in seen:
            seen.add(from_attendee["identifier"])
            cc.append(from_attendee)
    return cc


def reply_all_cc(
    email: dict[str, Any],
    *,
    primary_to: str,
    exclude_emails: set[str] | None = None,
) -> list[dict[str, str]]:
    """Build CC list from a message's to/cc/from attendees (Reply All minus primary To)."""
    return reply_all_cc_from_emails(
        [email],
        primary_to=primary_to,
        exclude_emails=exclude_emails,
    )
