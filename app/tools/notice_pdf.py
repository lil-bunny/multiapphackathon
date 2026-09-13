"""Generate customer shipment update notice PDF bytes."""

from __future__ import annotations

from fpdf import FPDF

from app.domain.shipment_row import ShipmentRow


def build_customer_notice_pdf(row: ShipmentRow, *, version: int) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Shipment Update Notice v{version}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)

    lines = [
        f"Shipment ID: {row.shipment_id}",
        f"Status: {row.status}",
        f"Original delivery: {row.delivery_date or '-'}",
        f"Current delivery: {row.current_delivery_datetime or row.delivery_date or '-'}",
        f"Delay reason: {row.delay_reason or '-'}",
        f"Driver: {row.driver_name or '-'}",
        f"Driver phone: {row.driver_phone or '-'}",
        f"Driver email: {row.driver_email or '-'}",
    ]
    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
