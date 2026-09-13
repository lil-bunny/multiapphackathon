"""Generate customer notice PDF and send via mail."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.logger import get_logger
from app.domain.shipment_row import ShipmentRow
from app.tools import mail as mail_tools
from app.tools import sheets as sheet_tools
from app.tools.notice_pdf import build_customer_notice_pdf

logger = get_logger(__name__)


class CustomerNoticeService:
    def publish_update(self, row: ShipmentRow) -> ShipmentRow:
        version = int(row.customer_notice_version or 0) + 1
        pdf_bytes = build_customer_notice_pdf(row, version=version)
        filename = f"customer_notice_v{version}.pdf"
        subject = f"Update: Shipment {row.shipment_id} - Delivery update"
        body = (
            f"Hi,\n\nYour shipment {row.shipment_id} delivery has been updated.\n"
            f"Original delivery: {row.delivery_date}\n"
            f"Current delivery: {row.current_delivery_datetime}\n"
            f"Reason: {row.delay_reason or 'See attached notice.'}\n\n"
            "Please see the attached Shipment Update Notice.\n"
        )
        patch: dict[str, str | int] = {"customer_notice_version": version}
        if row.customer_email:
            result = mail_tools.send_customer_email(
                to_email=row.customer_email,
                subject=subject,
                body=body,
                attachment_name=filename,
                attachment_bytes=pdf_bytes,
            )
            if result.get("success"):
                patch["last_customer_emailed_at"] = datetime.now(
                    timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                logger.warning(
                    "customer email failed shipment_id=%s error=%s",
                    row.shipment_id,
                    result.get("error"),
                )
        else:
            logger.warning(
                "customer email skipped shipment_id=%s (no customer_email on row)",
                row.shipment_id,
            )
        return sheet_tools.patch_row(row.shipment_id, patch)
