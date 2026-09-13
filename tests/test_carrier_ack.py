from app.core.config import settings
from app.domain.state import WorkflowState
from app.services.fixture_store import get_fixture_store
from app.workflows.graph import build_graph

settings.FIXTURE_MODE = True


def test_driver_details_sends_carrier_thanks() -> None:
    store = get_fixture_store()
    store.reset()
    store.load_rows(
        [
            {
                "shipment_id": "SHP-1042",
                "delivery_date": "2026-09-15 14:00",
                "current_delivery_datetime": "2026-09-15 14:00",
                "mail_thread_id": "thread-1042",
                "customer_email": "customer@example.com",
                "status": "pending",
            }
        ]
    )
    graph = build_graph()
    result = graph.invoke(
        WorkflowState(
            data={
                "event_type": "email_reply",
                "thread_id": "thread-1042",
                "email_id": "email-1",
                "subject": "Re: rate_confirmation SHP-1042",
                "fixture_thread_messages": [
                    {
                        "from": "carrier@example.com",
                        "subject": "Re: rate_confirmation SHP-1042",
                        "body": "Driver is John Smith, phone 555-0100, email john@carrier.com",
                    }
                ],
                "fixture_classification": {
                    "intent": "driver_details",
                    "driver": {
                        "name": "John Smith",
                        "phone": "555-0100",
                        "email": "john@carrier.com",
                    },
                    "delay": {},
                },
            }
        )
    )
    data = result.data if isinstance(result, WorkflowState) else result["data"]
    assert data.get("carrier_ack_sent") is True
    acks = [e for e in store.sent_emails if e.get("email_type") == "carrier_ack"]
    assert len(acks) == 1
    assert acks[0]["to"] == "carrier@example.com"
    assert "Thanks" in acks[0]["body"]
    assert data.get("delivery_followup_scheduled") is True
