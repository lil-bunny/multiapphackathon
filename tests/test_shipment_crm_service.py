from app.core.config import settings
from app.services.fixture_store import get_fixture_store
from app.services.shipment_crm_service import ShipmentCrmService

settings.FIXTURE_MODE = True


def setup_function() -> None:
    get_fixture_store().reset()


def test_upsert_assignment_enriches_preseeded_row() -> None:
    store = get_fixture_store()
    store.load_rows(
        [
            {
                "shipment_id": "SHP-2099",
                "delivery_date": "2026-09-15 14:00",
                "current_delivery_datetime": "2026-09-15 14:00",
                "customer_email": "customer@example.com",
                "mail_thread_id": "",
                "status": "pending",
            }
        ]
    )

    row = ShipmentCrmService().upsert_assignment(
        shipment_id="SHP-2099",
        delivery_date="2026-09-20 10:00",
        mail_thread_id="1a09c6244d844e20",
    )

    assert row.mail_thread_id == "1a09c6244d844e20"
    assert row.delivery_date == "2026-09-15 14:00"
    assert row.current_delivery_datetime == "2026-09-15 14:00"
    assert row.customer_email == "customer@example.com"
    assert row.status == "pending"


def test_upsert_assignment_overwrites_stale_thread_and_dates() -> None:
    store = get_fixture_store()
    store.load_rows(
        [
            {
                "shipment_id": "SHP-2099",
                "delivery_date": "2020-01-01 00:00",
                "current_delivery_datetime": "2020-01-01 00:00",
                "mail_thread_id": "abc-thread-123",
                "driver_name": "Old Driver",
                "status": "driver_assigned",
            }
        ]
    )

    row = ShipmentCrmService().upsert_assignment(
        shipment_id="SHP-2099",
        delivery_date="2026-09-15 14:00",
        mail_thread_id="1a09c6244d844e20",
    )

    assert row.mail_thread_id == "1a09c6244d844e20"
    assert row.delivery_date == "2026-09-15 14:00"
    assert row.current_delivery_datetime == "2026-09-15 14:00"
    assert row.driver_name == ""
    assert row.status == "pending"
