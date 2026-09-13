from app.services.shipment_crm_service import apply_delay_hours


def test_apply_delay_three_hours() -> None:
    assert apply_delay_hours("2026-09-15 14:00", "3") == "2026-09-15 17:00"
