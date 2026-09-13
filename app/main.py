from __future__ import annotations

import hashlib
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logger import get_logger
from app.domain.state import WorkflowState
from app.domain.unipile_webhook import parse_unipile_webhook_body
from app.services.ingress_guard import resolve_unipile_ingress
from app.workflows.graph import get_compiled_graph

logger = get_logger(__name__)
app = FastAPI(title="Multi-App Hackathon Agent")

_processed_keys: set[str] = set()


class RunRequest(BaseModel):
    event_type: str
    thread_id: str | None = None
    email_id: str | None = None
    attachment_id: str | None = None
    account_id: str | None = None
    pdf_bytes_path: str | None = None
    customer_email: str | None = None
    shipment_id: str | None = None
    subject: str | None = None
    fixture_thread_messages: list[dict[str, Any]] | None = None
    fixture_classification: dict[str, Any] | None = None
    fixture_pdf_extract: dict[str, Any] | None = None
    fixture_pdf_bytes: bytes | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def _run_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    graph = get_compiled_graph()
    state = WorkflowState(data=payload)
    result = graph.invoke(state)
    if isinstance(result, WorkflowState):
        return result.data
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return dict(result)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_workflow(body: RunRequest) -> dict[str, Any]:
    payload = body.model_dump(exclude_none=True)
    payload.update(payload.pop("extra", {}))
    return _run_workflow(payload)


@app.post("/webhook/unipile")
async def unipile_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    secret = settings.UNIPILE_WEBHOOK_SECRET
    if secret and x_webhook_secret != secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    payload = await parse_unipile_webhook_body(request)

    email_id = str(payload.get("email_id") or payload.get("id") or "")
    thread_id = str(payload.get("thread_id") or "")
    dedupe_key = hashlib.sha256(f"{email_id}:{thread_id}".encode()).hexdigest()
    if dedupe_key in _processed_keys:
        return {"status": "duplicate", "skipped": True}
    _processed_keys.add(dedupe_key)

    account_id = str(payload.get("account_id") or settings.UNIPILE_ACCOUNT_ID or "")
    decision = resolve_unipile_ingress(payload, account_id=account_id)

    if decision.action == "ignore":
        logger.info("webhook ignored reason=%s thread_id=%s", decision.skip_reason, thread_id)
        return {"status": "ignored", "reason": decision.skip_reason}

    assert decision.run_payload is not None
    logger.info(
        "webhook event_type=%s thread_id=%s",
        decision.run_payload.get("event_type"),
        thread_id,
    )
    return {"status": "accepted", "result": _run_workflow(decision.run_payload)}
