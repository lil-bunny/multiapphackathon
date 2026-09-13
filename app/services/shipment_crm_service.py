"""Sheet CRM orchestration: match rows, apply driver/delay patches."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.domain.reply_intent import DELIVERY_DELAY, DELIVERY_STATUS, DRIVER_DETAILS
from app.domain.shipment_row import ShipmentRow
from app.tools import sheets as sheet_tools


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def apply_delay_hours(base: str, hours: str | None) -> str:
    dt = _parse_datetime(base)
    if not dt:
        return base
    try:
        delta = float(str(hours or "0"))
    except ValueError:
        return base
    return (dt + timedelta(hours=delta)).strftime("%Y-%m-%d %H:%M")


class ShipmentCrmService:
    def match_row(
        self,
        *,
        thread_id: str | None = None,
        shipment_id: str | None = None,
    ) -> ShipmentRow | None:
        if thread_id:
            row = sheet_tools.read_row_by_thread_id(thread_id)
            if row:
                return row
        if shipment_id:
            return sheet_tools.read_row_by_shipment_id(shipment_id)
        return None

    def upsert_assignment(
        self,
        *,
        shipment_id: str,
        delivery_date: str,
        mail_thread_id: str = "",
        customer_email: str = "",
        assignment_pdf_link: str = "",
    ) -> ShipmentRow:
        existing = sheet_tools.read_row_by_shipment_id(shipment_id)
        if existing:
            row = existing
            preseeded = not str(existing.mail_thread_id or "").strip()
            if mail_thread_id:
                row.mail_thread_id = mail_thread_id
            if assignment_pdf_link:
                row.assignment_pdf_link = assignment_pdf_link
            if customer_email and not row.customer_email:
                row.customer_email = customer_email

            if preseeded:
                # Row already in sheet — only fill blanks from the ratecon email.
                if delivery_date and not row.delivery_date:
                    row.delivery_date = delivery_date
                if delivery_date and not row.current_delivery_datetime:
                    row.current_delivery_datetime = delivery_date
                if not row.status:
                    row.status = "pending"
            else:
                # Re-ratecon on a linked row — refresh dates and restart workflow.
                if delivery_date:
                    row.delivery_date = delivery_date
                    row.current_delivery_datetime = delivery_date
                row.driver_name = ""
                row.driver_email = ""
                row.driver_phone = ""
                row.delay_reason = ""
                row.status = "pending"
        else:
            row = ShipmentRow(
                shipment_id=shipment_id,
                delivery_date=delivery_date,
                current_delivery_datetime=delivery_date,
                mail_thread_id=mail_thread_id,
                customer_email=customer_email,
                assignment_pdf_link=assignment_pdf_link,
                status="pending",
            )
        return sheet_tools.upsert_row(row)

    def apply_reply_update(
        self,
        *,
        row: ShipmentRow,
        intent: str,
        driver: dict[str, str | None],
        delay: dict[str, str | None],
    ) -> tuple[ShipmentRow, bool, bool, bool]:
        """Return updated row, notify customer, driver ack, and on-track ack flags."""
        patch: dict[str, Any] = {}
        notify = False
        ack_carrier = False
        ack_on_track = False

        if intent == DRIVER_DETAILS:
            if not row.driver_name and driver.get("name"):
                patch["driver_name"] = driver["name"]
            if not row.driver_email and driver.get("email"):
                patch["driver_email"] = driver["email"]
            if not row.driver_phone and driver.get("phone"):
                patch["driver_phone"] = driver["phone"]
            if patch:
                patch["status"] = "driver_assigned"
                ack_carrier = True

        if intent == DELIVERY_DELAY:
            new_dt = delay.get("new_delivery_datetime")
            if not new_dt:
                base = row.current_delivery_datetime or row.delivery_date
                new_dt = apply_delay_hours(base, delay.get("delay_hours"))
            patch["current_delivery_datetime"] = new_dt
            patch["delay_reason"] = delay.get("reason") or ""
            patch["status"] = "delayed"
            notify = bool(new_dt and patch["delay_reason"])

        if intent == DELIVERY_STATUS:
            patch["status"] = "on_track"
            ack_on_track = True

        if not patch:
            return row, notify, ack_carrier, ack_on_track
        updated = sheet_tools.patch_row(row.shipment_id, patch)
        return updated, notify, ack_carrier, ack_on_track
