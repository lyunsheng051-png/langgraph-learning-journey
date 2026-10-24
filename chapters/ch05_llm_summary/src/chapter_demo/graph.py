from typing import Literal

from langgraph.graph import END, START, StateGraph

from .model_adapter import SummaryContext
from .nodes import accept_summary, generate_summary, read_document, reject_summary, validate_summary
from .state import SummaryState


def route_after_step(state: SummaryState) -> Literal["ready", "reject"]:
    return "reject" if state.get("error") else "ready"


def build_graph():
    builder = StateGraph(SummaryState, context_schema=SummaryContext)
    for name, node in (("read_document", read_document), ("generate_summary", generate_summary),
                       ("validate_summary", validate_summary), ("accept_summary", accept_summary),
                       ("reject_summary", reject_summary)):
        builder.add_node(name, node)
    builder.add_edge(START, "read_document")
    for current, following in (("read_document", "generate_summary"),
                               ("generate_summary", "validate_summary"),
                               ("validate_summary", "accept_summary")):
        builder.add_conditional_edges(current, route_after_step, {"ready": following, "reject": "reject_summary"})
    builder.add_edge("accept_summary", END)
    builder.add_edge("reject_summary", END)
    return builder.compile()
