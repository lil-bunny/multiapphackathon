from app.domain.shipment_row import ShipmentRow
from app.tools.notice_pdf import build_customer_notice_pdf


def test_notice_pdf_bytes() -> None:
    row = ShipmentRow(
        shipment_id="SHP-1",
        delivery_date="2026-09-15 14:00",
        current_delivery_datetime="2026-09-15 17:00",
        delay_reason="Rain",
    )
    pdf = build_customer_notice_pdf(row, version=1)
    assert pdf.startswith(b"%PDF")
