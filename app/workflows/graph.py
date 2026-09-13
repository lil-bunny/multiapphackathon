from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.configs.workflow_config import WORKFLOW_CONFIG
from app.domain.state import WorkflowState
from app.workflows.registry import NODE_REGISTRY
from app.workflows.routers import classification_router, crm_next_router, event_type_router

ROUTER_REGISTRY = {
    "event_type": event_type_router,
    "classification": classification_router,
    "crm_next": crm_next_router,
    "always_end": lambda _state: "end",
}


def build_graph():
    graph = StateGraph(WorkflowState)

    for node in WORKFLOW_CONFIG["nodes"]:
        graph.add_node(node, NODE_REGISTRY[node])

    for src, dst in WORKFLOW_CONFIG["edges"]:
        graph.add_edge(src, dst)

    for node, router_def in WORKFLOW_CONFIG["routers"].items():
        router_fn = ROUTER_REGISTRY[router_def["router"]]
        graph.add_conditional_edges(node, router_fn, router_def["map"])

    graph.set_entry_point(WORKFLOW_CONFIG["entry"])
    graph.add_edge(WORKFLOW_CONFIG["exit"], END)
    return graph.compile()


_compiled = None


def get_compiled_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled
