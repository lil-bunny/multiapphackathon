from app.core.logger import get_logger
from app.domain.reply_intent import DELIVERY_DELAY, DO_NOTHING, INSUFFICIENT
from app.domain.state import WorkflowState
from app.services.shipment_crm_service import ShipmentCrmService
from app.services.slack_alert_service import SlackAlertService

logger = get_logger(__name__)


def apply_crm_update(state: WorkflowState) -> WorkflowState:
    data = state.data
    intent = str(data.get("reply_intent") or DO_NOTHING)
    if intent in {DO_NOTHING, INSUFFICIENT}:
        state.data["should_notify_customer"] = False
        return state

    classification = data.get("classification") or {}
    crm = ShipmentCrmService()
    row = crm.match_row(
        thread_id=str(data.get("thread_id") or ""),
        shipment_id=str(data.get("shipment_id") or ""),
    )
    if not row:
        state.data["workflow_error"] = "crm_row_not_found"
        return state

    updated, notify, ack_carrier, ack_on_track = crm.apply_reply_update(
        row=row,
        intent=intent,
        driver=classification.get("driver") or {},
        delay=classification.get("delay") or {},
    )
    state.data["shipment_id"] = updated.shipment_id
    state.data["crm_row"] = updated.to_sheet_dict()
    state.data["should_notify_customer"] = notify
    state.data["should_ack_carrier"] = ack_carrier
    state.data["should_ack_on_track"] = ack_on_track
    if intent == DELIVERY_DELAY and notify:
        SlackAlertService().send_delay_alert(updated)
    logger.info(
        "crm updated shipment_id=%s intent=%s notify=%s",
        updated.shipment_id,
        intent,
        notify,
    )
    return state
