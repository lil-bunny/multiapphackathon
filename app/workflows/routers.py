"""Pure routers: state -> route key (no I/O)."""

from __future__ import annotations

from app.domain.reply_intent import (
    DELIVERY_DELAY,
    DELIVERY_STATUS,
    DO_NOTHING,
    DRIVER_DETAILS,
    INSUFFICIENT,
)
from app.domain.state import WorkflowState


def event_type_router(state: WorkflowState) -> str:
    event_type = str(state.data.get("event_type") or "").strip()
    if event_type == "pdf_assignment":
        return "pdf_assignment"
    if event_type == "email_reply":
        return "email_reply"
    return "unknown"


def classification_router(state: WorkflowState) -> str:
    intent = str(state.data.get("reply_intent") or DO_NOTHING).strip()
    if intent == DRIVER_DETAILS:
        return "driver_details"
    if intent == DELIVERY_DELAY:
        return "delivery_delay"
    if intent == DELIVERY_STATUS:
        return "delivery_status"
    if intent == INSUFFICIENT:
        return "insufficient"
    return "skip"


def crm_next_router(state: WorkflowState) -> str:
    if state.data.get("should_ack_carrier"):
        return "ack"
    if state.data.get("should_ack_on_track"):
        return "on_track_ack"
    if state.data.get("should_notify_customer"):
        return "notify"
    return "end"
