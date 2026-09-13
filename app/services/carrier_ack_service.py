"""Send thank-you reply to carrier after driver details are saved."""

from __future__ import annotations

from app.domain.shipment_row import ShipmentRow
from app.tools import mail as mail_tools


class CarrierAckService:
    def send_driver_details_thanks(
        self,
        *,
        row: ShipmentRow,
        subject: str = "",
        email_id: str | None = None,
        account_id: str | None = None,
        thread_id: str | None = None,
        thread_messages: list[dict] | None = None,
        carrier_email: str | None = None,
    ) -> dict:
        to_email = (carrier_email or "").strip()
        if not to_email and thread_messages:
            to_email = mail_tools.carrier_email_from_thread_messages(thread_messages) or ""
        if not to_email:
            return {"success": False, "error": "carrier_email_missing"}

        body = (
            f"Thanks — we received driver details for shipment {row.shipment_id}.\n\n"
            f"Driver: {row.driver_name or '-'}\n"
            f"Phone: {row.driver_phone or '-'}\n"
            f"Email: {row.driver_email or '-'}\n"
        )
        return mail_tools.send_carrier_thread_reply(
            to_email=to_email,
            subject=mail_tools.reply_subject(subject, row.shipment_id),
            body=body,
            reply_to_email_id=email_id,
            account_id=account_id,
            thread_id=thread_id,
        )

    def send_on_track_confirmation(
        self,
        *,
        row: ShipmentRow,
        subject: str = "",
        email_id: str | None = None,
        account_id: str | None = None,
        thread_id: str | None = None,
        thread_messages: list[dict] | None = None,
        carrier_email: str | None = None,
    ) -> dict:
        to_email = (carrier_email or "").strip()
        if not to_email and thread_messages:
            to_email = mail_tools.carrier_email_from_thread_messages(thread_messages) or ""
        if not to_email:
            return {"success": False, "error": "carrier_email_missing"}

        eta = row.current_delivery_datetime or row.delivery_date
        body = (
            f"Thanks — noted on-time delivery for shipment {row.shipment_id}.\n\n"
            f"Expected delivery window: {eta}\n"
            "We have recorded status as on track."
        )
        return mail_tools.send_thread_reply(
            to_email=to_email,
            subject=mail_tools.reply_subject(subject, row.shipment_id),
            body=body,
            reply_to_email_id=email_id,
            account_id=account_id,
            thread_id=thread_id,
            email_type="carrier_on_track_ack",
        )
