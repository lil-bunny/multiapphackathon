from __future__ import annotations

from pydantic import BaseModel, Field

SHEET_COLUMNS: list[str] = [
    "shipment_id",
    "delivery_date",
    "current_delivery_datetime",
    "delay_reason",
    "driver_name",
    "driver_email",
    "driver_phone",
    "mail_thread_id",
    "customer_email",
    "assignment_pdf_link",
    "latest_notice_link",
    "customer_notice_version",
    "status",
    "last_customer_emailed_at",
]


class ShipmentRow(BaseModel):
    shipment_id: str
    delivery_date: str = ""
    current_delivery_datetime: str = ""
    delay_reason: str = ""
    driver_name: str = ""
    driver_email: str = ""
    driver_phone: str = ""
    mail_thread_id: str = ""
    customer_email: str = ""
    assignment_pdf_link: str = ""
    latest_notice_link: str = ""
    customer_notice_version: int = 0
    status: str = "pending"
    last_customer_emailed_at: str = ""

    def to_sheet_dict(self) -> dict[str, str | int]:
        return self.model_dump()

    @classmethod
    def from_sheet_dict(cls, data: dict) -> ShipmentRow:
        clean = {k: data.get(k, "") for k in SHEET_COLUMNS}
        for email_key in ("customer_email", "driver_email"):
            clean[email_key] = str(clean.get(email_key) or "").strip()
        version = clean.get("customer_notice_version", 0)
        try:
            clean["customer_notice_version"] = int(version or 0)
        except (TypeError, ValueError):
            clean["customer_notice_version"] = 0
        return cls(**clean)
