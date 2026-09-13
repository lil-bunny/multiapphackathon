"""Schedule and send delivery status check after driver ack."""

from __future__ import annotations

import threading
import time
from typing import Any

from app.core.config import settings
from app.core.logger import get_logger
from app.domain.shipment_row import ShipmentRow
from app.services.fixture_store import get_fixture_store
from app.tools import mail as mail_tools
from app.tools import sheets as sheet_tools

logger = get_logger(__name__)

AWAITING_DELIVERY_STATUS = "awaiting_delivery_status"


class DeliveryFollowUpService:
    def schedule_status_check(
        self,
        *,
        shipment_id: str,
        thread_id: str,
        reply_to_email_id: str,
        account_id: str | None,
        subject: str,
        carrier_email: str,
    ) -> None:
        delay = max(0, int(settings.DELIVERY_FOLLOWUP_DELAY_SECONDS))
        payload = {
            "shipment_id": shipment_id,
            "thread_id": thread_id,
            "reply_to_email_id": reply_to_email_id,
            "account_id": account_id,
            "subject": subject,
            "carrier_email": carrier_email,
        }

        def _run() -> None:
            if delay:
                time.sleep(delay)
            self.send_status_check(**payload)

        threading.Thread(target=_run, daemon=True).start()
        logger.info(
            "scheduled delivery status followup shipment_id=%s delay_s=%s",
            shipment_id,
            delay,
        )

    def send_status_check(
        self,
        *,
        shipment_id: str,
        thread_id: str,
        reply_to_email_id: str,
        account_id: str | None,
        subject: str,
        carrier_email: str,
    ) -> dict[str, Any]:
        row = sheet_tools.read_row_by_shipment_id(shipment_id)
        if not row:
            return {"success": False, "error": "shipment_not_found"}
        if row.status in {AWAITING_DELIVERY_STATUS, "delayed", "on_track"}:
            return {"success": False, "error": "followup_already_sent", "skipped": True}
        if row.status != "driver_assigned":
            return {"success": False, "error": "not_ready_for_followup", "skipped": True}

        eta = row.current_delivery_datetime or row.delivery_date
        body = (
            f"Delivery window for shipment {shipment_id} is approaching ({eta}).\n\n"
            "Please confirm on-time delivery or report any delay."
        )
        result = mail_tools.send_thread_reply(
            to_email=carrier_email,
            subject=mail_tools.reply_subject(subject, shipment_id),
            body=body,
            reply_to_email_id=reply_to_email_id or None,
            account_id=account_id,
            thread_id=thread_id,
            email_type="delivery_followup",
        )
        if result.get("success"):
            sheet_tools.patch_row(
                shipment_id,
                {"status": AWAITING_DELIVERY_STATUS},
            )
            logger.info("delivery status followup sent shipment_id=%s", shipment_id)
        else:
            logger.warning(
                "delivery status followup failed shipment_id=%s error=%s",
                shipment_id,
                result.get("error"),
            )
        return result
