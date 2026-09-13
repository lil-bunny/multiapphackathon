from app.domain.state import WorkflowState
from app.workflows.routers import classification_router, crm_next_router, event_type_router


def test_event_type_router() -> None:
    state = WorkflowState(data={"event_type": "pdf_assignment"})
    assert event_type_router(state) == "pdf_assignment"


def test_classification_router_delay() -> None:
    state = WorkflowState(data={"reply_intent": "delivery_delay"})
    assert classification_router(state) == "delivery_delay"


def test_classification_router_delivery_status() -> None:
    state = WorkflowState(data={"reply_intent": "delivery_status"})
    assert classification_router(state) == "delivery_status"


def test_crm_next_router() -> None:
    state = WorkflowState(data={"should_notify_customer": True})
    assert crm_next_router(state) == "notify"
    ack = WorkflowState(data={"should_ack_carrier": True})
    assert crm_next_router(ack) == "ack"
    on_track = WorkflowState(data={"should_ack_on_track": True})
    assert crm_next_router(on_track) == "on_track_ack"
