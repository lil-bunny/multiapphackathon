from app.domain.guards import (
    can_process_email_reply,
    can_start_pdf_assignment,
    find_rate_confirmation_attachment,
    is_rate_confirmation_attachment,
    is_rate_confirmation_subject,
)
from app.services.ingress_guard import resolve_unipile_ingress


def test_rate_confirmation_pdf_matches() -> None:
    assert is_rate_confirmation_attachment("rate_confirmation.pdf")
    assert is_rate_confirmation_attachment("rate_confirmation_2099.pdf")
    assert is_rate_confirmation_attachment("Rate_Confirmation.PDF")
    assert not is_rate_confirmation_attachment("assignment.pdf")
    assert not is_rate_confirmation_attachment("rate_confirmation.txt")


def test_rate_confirmation_subject_accepts_spaces() -> None:
    assert is_rate_confirmation_subject("Rate confirmation")
    assert is_rate_confirmation_subject("Rate confirmation shp-2099")
    assert is_rate_confirmation_subject("rate_confirmation SHP-1")


def test_find_rate_confirmation_attachment() -> None:
    attachments = [
        {"name": "other.pdf", "id": "1"},
        {"name": "rate_confirmation.pdf", "id": "2"},
    ]
    found = find_rate_confirmation_attachment(attachments)
    assert found is not None
    assert found["id"] == "2"


def test_can_start_pdf_assignment_requires_rate_confirmation_pdf() -> None:
    att, reason = can_start_pdf_assignment([{"name": "invoice.pdf", "id": "1"}])
    assert att is None
    assert reason == "not_rate_confirmation_pdf"


def test_can_process_email_reply_by_subject_or_thread() -> None:
    assert can_process_email_reply(subject="rate_confirmation SHP-1", thread_id="", thread_has_crm_row=False) is None
    assert can_process_email_reply(subject="hello", thread_id="t1", thread_has_crm_row=True) is None
    assert (
        can_process_email_reply(subject="hello", thread_id="t1", thread_has_crm_row=False)
        == "not_rate_confirmation_thread"
    )


def test_resolve_unipile_ingress_pdf_path() -> None:
    decision = resolve_unipile_ingress(
        {
            "email_id": "e1",
            "thread_id": "t1",
            "subject": "rate_confirmation SHP-1",
            "attachments": [{"name": "rate_confirmation.pdf", "id": "a1"}],
        },
        account_id="acc1",
    )
    assert decision.action == "pdf_assignment"
    assert decision.run_payload["attachment_id"] == "a1"


def test_resolve_unipile_ingress_ignores_other_pdf() -> None:
    decision = resolve_unipile_ingress(
        {
            "email_id": "e1",
            "thread_id": "t1",
            "subject": "invoice",
            "attachments": [{"name": "invoice.pdf", "id": "a1"}],
        },
        account_id="acc1",
    )
    assert decision.action == "ignore"
    assert decision.skip_reason == "not_rate_confirmation_thread"


def test_resolve_unipile_ingress_reply_by_subject() -> None:
    decision = resolve_unipile_ingress(
        {
            "email_id": "e2",
            "thread_id": "t2",
            "subject": "Re: rate_confirmation SHP-1",
            "attachments": [],
        },
        account_id="acc1",
    )
    assert decision.action == "email_reply"


def test_resolve_unipile_ingress_pdf_with_numbered_filename() -> None:
    decision = resolve_unipile_ingress(
        {
            "email_id": "e3",
            "thread_id": "t3",
            "subject": "Rate confirmation",
            "attachments": [{"name": "rate_confirmation_2099.pdf", "id": "a3"}],
        },
        account_id="acc1",
    )
    assert decision.action == "pdf_assignment"
