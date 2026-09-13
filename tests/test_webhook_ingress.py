"""Unipile webhook HTTP body parsing and ingress."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.config import settings
from app.domain.unipile_webhook import normalize_attachments, normalize_form_payload
from app.main import app
from app.services.fixture_store import get_fixture_store
from app.services.ingress_guard import resolve_unipile_ingress

settings.FIXTURE_MODE = True

client = TestClient(app)


def setup_function() -> None:
    get_fixture_store().reset()


def test_normalize_attachments_from_json_string() -> None:
    raw = '[{"id":"a1","name":"rate_confirmation_2099.pdf"}]'
    assert normalize_attachments(raw)[0]["name"] == "rate_confirmation_2099.pdf"


def test_normalize_form_payload_decodes_attachments() -> None:
    attachments = [{"id": "att-1", "name": "rate_confirmation.pdf"}]
    payload = normalize_form_payload(
        {
            "event": ["mail_received"],
            "email_id": ["e1"],
            "attachments": [json.dumps(attachments)],
        }
    )
    assert payload["event"] == "mail_received"
    assert payload["attachments"] == attachments


def test_webhook_accepts_json_body() -> None:
    resp = client.post(
        "/webhook/unipile",
        json={
            "event": "mail_received",
            "email_id": "test-email-001",
            "thread_id": "thread-unknown",
            "subject": "hello",
            "attachments": [],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_webhook_accepts_form_encoded_body() -> None:
    resp = client.post(
        "/webhook/unipile",
        data={
            "event": "mail_received",
            "email_id": "test-email-form",
            "account_id": "acct-001",
            "thread_id": "thread-unknown",
            "subject": "hello",
            "attachments": json.dumps([]),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_webhook_json_body_with_form_content_type() -> None:
    payload = {
        "event": "mail_received",
        "email_id": "aaBc5zx6UuCW72zr44boGw",
        "account_id": "acct-001",
        "thread_id": "1a09c6244d844e20",
        "subject": "Rate confirmation",
        "has_attachments": True,
        "attachments": [
            {
                "id": "att-2099",
                "name": "rate_confirmation_2099.pdf",
                "extension": "pdf",
                "mime": "application/pdf",
            }
        ],
    }
    resp = client.post(
        "/webhook/unipile",
        content=json.dumps(payload),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_form_payload_routes_rate_confirmation_pdf() -> None:
    attachments = [
        {
            "id": "att-1",
            "name": "rate_confirmation.pdf",
            "extension": "pdf",
            "mime": "application/pdf",
        }
    ]
    payload = normalize_form_payload(
        {
            "event": ["mail_received"],
            "email_id": ["test-email-pdf"],
            "account_id": ["acct-001"],
            "thread_id": ["thread-pdf"],
            "subject": ["Rate confirmation shp-2099"],
            "attachments": [json.dumps(attachments)],
        }
    )
    decision = resolve_unipile_ingress(payload, account_id="acct-001")
    assert decision.action == "pdf_assignment"
    assert decision.run_payload is not None
    assert decision.run_payload["event_type"] == "pdf_assignment"
