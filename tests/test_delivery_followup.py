from app.core.config import settings
from app.services.delivery_followup_service import (
    AWAITING_DELIVERY_STATUS,
    DeliveryFollowUpService,
)
from app.services.fixture_store import get_fixture_store

settings.FIXTURE_MODE = True
settings.DELIVERY_FOLLOWUP_DELAY_SECONDS = 0


def setup_function() -> None:
    get_fixture_store().reset()


def test_send_status_check_updates_sheet_and_sends_mail() -> None:
    store = get_fixture_store()
    store.load_rows(
        [
            {
                "shipment_id": "SHP-2099",
                "delivery_date": "2026-09-15 14:00",
                "current_delivery_datetime": "2026-09-15 14:00",
                "mail_thread_id": "thread-2099",
                "status": "driver_assigned",
            }
        ]
    )
    result = DeliveryFollowUpService().send_status_check(
        shipment_id="SHP-2099",
        thread_id="thread-2099",
        reply_to_email_id="email-2",
        account_id="acct-1",
        subject="Re: Rate confirmation",
        carrier_email="carrier@example.com",
    )
    assert result["success"] is True
    row = store.rows["SHP-2099"]
    assert row["status"] == AWAITING_DELIVERY_STATUS
    followups = [e for e in store.sent_emails if e.get("email_type") == "delivery_followup"]
    assert len(followups) == 1
    assert "approaching" in followups[0]["body"].lower()
