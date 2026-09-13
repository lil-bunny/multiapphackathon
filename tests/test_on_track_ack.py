from app.core.config import settings
from app.domain.state import WorkflowState
from app.services.fixture_store import get_fixture_store
from app.workflows.graph import build_graph

settings.FIXTURE_MODE = True


def test_delivery_status_sends_on_track_confirmation() -> None:
    store = get_fixture_store()
    store.reset()
    store.load_rows(
        [
            {
                "shipment_id": "SHP-2099",
                "delivery_date": "2026-09-15 14:00",
                "current_delivery_datetime": "2026-09-15 14:00",
                "mail_thread_id": "thread-2099",
                "status": "awaiting_delivery_status",
            }
        ]
    )
    graph = build_graph()
    result = graph.invoke(
        WorkflowState(
            data={
                "event_type": "email_reply",
                "thread_id": "thread-2099",
                "email_id": "email-3",
                "subject": "Re: Rate confirmation",
                "fixture_thread_messages": [
                    {
                        "from": "carrier@example.com",
                        "subject": "Re: Rate confirmation",
                        "body": "On time for the delivery window.",
                    }
                ],
                "fixture_classification": {
                    "intent": "delivery_status",
                    "driver": {},
                    "delay": {},
                },
            }
        )
    )
    data = result.data if isinstance(result, WorkflowState) else result["data"]
    assert data.get("on_track_ack_sent") is True
    assert data["crm_row"]["status"] == "on_track"
    acks = [e for e in store.sent_emails if e.get("email_type") == "carrier_on_track_ack"]
    assert len(acks) == 1
    assert "on-time" in acks[0]["body"].lower() or "on track" in acks[0]["body"].lower()
