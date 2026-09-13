from app.domain.state import WorkflowState


def route_event(state: WorkflowState) -> WorkflowState:
    return state
