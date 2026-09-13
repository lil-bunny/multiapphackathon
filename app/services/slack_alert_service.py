"""Post operational alerts to Slack."""

from __future__ import annotations

from app.core.logger import get_logger
from app.domain.shipment_row import ShipmentRow
from app.tools import slack as slack_tools

logger = get_logger(__name__)


class SlackAlertService:
    def send_delay_alert(self, row: ShipmentRow) -> None:
        text = (
            f":warning: Delay alert for shipment *{row.shipment_id}*\n"
            f"New delivery: {row.current_delivery_datetime or '-'}\n"
            f"Reason: {row.delay_reason or 'Not specified'}"
        )
        slack_tools.send_webhook_alert(text)
        logger.info("slack delay alert shipment_id=%s", row.shipment_id)
