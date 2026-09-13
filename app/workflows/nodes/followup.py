from app.core.logger import get_logger
from app.domain.state import WorkflowState
from app.services.delivery_followup_service import DeliveryFollowUpService
from app.tools import mail as mail_tools

logger = get_logger(__name__)


def schedule_delivery_followup(state: WorkflowState) -> WorkflowState:
    data = state.data
    if not data.get("carrier_ack_sent"):
        return state

    crm_row = data.get("crm_row") or {}
    shipment_id = str(crm_row.get("shipment_id") or data.get("shipment_id") or "")
    thread_id = str(data.get("thread_id") or "")
    email_id = str(data.get("email_id") or "")
    if not shipment_id or not thread_id or not email_id:
        state.data["delivery_followup_error"] = "missing_followup_context"
        return state

    messages = mail_tools.fetch_thread_messages(
        thread_id=thread_id,
        account_id=data.get("account_id"),
        fixture_messages=data.get("fixture_thread_messages"),
    )
    carrier_email = (
        str(data.get("carrier_email") or "").strip()
        or mail_tools.carrier_email_from_thread_messages(messages)
        or str(crm_row.get("driver_email") or "").strip()
    )
    if not carrier_email:
        state.data["delivery_followup_error"] = "carrier_email_missing"
        return state

    DeliveryFollowUpService().schedule_status_check(
        shipment_id=shipment_id,
        thread_id=thread_id,
        reply_to_email_id=email_id,
        account_id=data.get("account_id"),
        subject=str(data.get("subject") or ""),
        carrier_email=carrier_email,
    )
    state.data["delivery_followup_scheduled"] = True
    logger.info("delivery followup scheduled shipment_id=%s", shipment_id)
    return state
