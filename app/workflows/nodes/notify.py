from __future__ import annotations

from app.core.logger import get_logger
from app.domain.shipment_row import ShipmentRow
from app.domain.state import WorkflowState
from app.services.customer_notice_service import CustomerNoticeService

logger = get_logger(__name__)


def notify_customer(state: WorkflowState) -> WorkflowState:
    crm_row = state.data.get("crm_row")
    if not isinstance(crm_row, dict):
        state.data["workflow_error"] = "missing_crm_row_for_notify"
        return state
    row = CustomerNoticeService().publish_update(ShipmentRow.from_sheet_dict(crm_row))
    state.data["crm_row"] = row.to_sheet_dict()
    emailed = bool(row.last_customer_emailed_at)
    state.data["customer_notified"] = emailed
    if emailed:
        logger.info("customer notified shipment_id=%s", row.shipment_id)
    else:
        logger.warning("customer notify incomplete shipment_id=%s", row.shipment_id)
    return state


def end(state: WorkflowState) -> WorkflowState:
    return state
