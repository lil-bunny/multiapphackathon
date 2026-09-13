"""Pure helpers for reply LLM output parsing (no I/O)."""

from __future__ import annotations

from typing import Any

from app.domain.reply_intent import (
    DELIVERY_DELAY,
    DELIVERY_STATUS,
    DO_NOTHING,
    DRIVER_DETAILS,
    INSUFFICIENT,
    VALID_INTENTS,
)


def _clean_field(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "null":
        return None
    return text


def normalize_driver_block(raw: Any) -> dict[str, str | None]:
    if not isinstance(raw, dict):
        return {"name": None, "phone": None, "email": None}
    return {
        "name": _clean_field(raw.get("name")),
        "phone": _clean_field(raw.get("phone")),
        "email": _clean_field(raw.get("email")),
    }


def normalize_intent(raw: dict[str, Any]) -> str:
    intent = str(raw.get("intent") or raw.get("decision") or "").strip().lower()
    if intent in VALID_INTENTS:
        return intent
    return DO_NOTHING


def validate_driver_fields(driver: dict[str, str | None]) -> str:
    name = driver.get("name")
    phone = driver.get("phone")
    email = driver.get("email")
    if name and (phone or email):
        return DRIVER_DETAILS
    if name or phone or email:
        return INSUFFICIENT
    return DO_NOTHING


def normalize_delay_block(raw: Any) -> dict[str, str | None]:
    if not isinstance(raw, dict):
        return {
            "new_delivery_datetime": None,
            "delay_hours": None,
            "reason": None,
        }
    return {
        "new_delivery_datetime": _clean_field(raw.get("new_delivery_datetime")),
        "delay_hours": _clean_field(raw.get("delay_hours")),
        "reason": _clean_field(raw.get("reason")),
    }


def validate_delay_fields(delay: dict[str, str | None]) -> str:
    if delay.get("new_delivery_datetime") or delay.get("delay_hours"):
        if delay.get("reason"):
            return DELIVERY_DELAY
        return INSUFFICIENT
    return DO_NOTHING


def build_reply_classification_result(raw: dict[str, Any]) -> dict[str, Any]:
    intent = normalize_intent(raw)
    driver = normalize_driver_block(raw.get("driver"))
    delay = normalize_delay_block(raw.get("delay"))

    if intent == DRIVER_DETAILS:
        intent = validate_driver_fields(driver)
    elif intent == DELIVERY_DELAY:
        intent = validate_delay_fields(delay)
    elif intent == DELIVERY_STATUS:
        intent = DELIVERY_STATUS
    else:
        intent = DO_NOTHING if intent not in {INSUFFICIENT} else intent

    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "intent": intent,
        "confidence": confidence,
        "reason": str(raw.get("reason") or "").strip() or "no reason",
        "driver": driver,
        "delay": delay,
    }


def format_thread_for_llm(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for msg in messages:
        sender = _clean_field(msg.get("from")) or "unknown"
        subject = _clean_field(msg.get("subject")) or ""
        body = str(msg.get("body") or msg.get("body_plain") or "").strip()
        parts.append(f"From: {sender}\nSubject: {subject}\n{body}")
    return "\n\n---\n\n".join(parts)
