from app.workflows.nodes.ack import send_driver_details_ack
from app.workflows.nodes.assignment import process_assignment_pdf
from app.workflows.nodes.crm import apply_crm_update
from app.workflows.nodes.followup import schedule_delivery_followup
from app.workflows.nodes.on_track_ack import send_on_track_carrier_ack
from app.workflows.nodes.ingress import route_event
from app.workflows.nodes.notify import end, notify_customer
from app.workflows.nodes.reply import classify_email_reply

NODE_REGISTRY = {
    "route_event": route_event,
    "process_assignment_pdf": process_assignment_pdf,
    "classify_email_reply": classify_email_reply,
    "apply_crm_update": apply_crm_update,
    "send_driver_details_ack": send_driver_details_ack,
    "schedule_delivery_followup": schedule_delivery_followup,
    "send_on_track_carrier_ack": send_on_track_carrier_ack,
    "notify_customer": notify_customer,
    "end": end,
}
