from app.core.logger import get_logger
from app.domain.shipment_row import ShipmentRow
from app.domain.state import WorkflowState
from app.services.carrier_ack_service import CarrierAckService
from app.tools import mail as mail_tools

logger = get_logger(__name__)


def send_on_track_carrier_ack(state: WorkflowState) -> WorkflowState:
    crm_row = state.data.get("crm_row")
    if not isinstance(crm_row, dict):
        state.data["workflow_error"] = "missing_crm_row_for_on_track_ack"
        return state

    data = state.data
    messages = mail_tools.fetch_thread_messages(
        thread_id=str(data.get("thread_id") or ""),
        account_id=data.get("account_id"),
        fixture_messages=data.get("fixture_thread_messages"),
    )
    result = CarrierAckService().send_on_track_confirmation(
        row=ShipmentRow.from_sheet_dict(crm_row),
        subject=str(data.get("subject") or ""),
        email_id=str(data.get("email_id") or "") or None,
        account_id=data.get("account_id"),
        thread_id=str(data.get("thread_id") or "") or None,
        thread_messages=messages,
        carrier_email=str(data.get("carrier_email") or "") or None,
    )
    state.data["on_track_ack_sent"] = bool(result.get("success"))
    if not result.get("success"):
        state.data["on_track_ack_error"] = str(result.get("error") or "send_failed")
    logger.info(
        "on-track ack shipment_id=%s sent=%s",
        crm_row.get("shipment_id"),
        state.data["on_track_ack_sent"],
    )
    return state
