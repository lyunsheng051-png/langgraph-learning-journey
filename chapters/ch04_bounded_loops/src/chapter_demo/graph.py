from typing import Literal

from langgraph.graph import END, START, StateGraph

from .nodes import accept_report, check_report, prepare_report, repair_report, stop_repairing
from .state import ReportState


def route_after_check(state: ReportState) -> Literal["accepted", "repair", "exhausted"]:
    if not state["issues"]:
        return "accepted"
    if state["repairs"] >= state["max_repairs"]:
        return "exhausted"
    return "repair"


def build_graph():
    builder = StateGraph(ReportState)
    builder.add_node("prepare_report", prepare_report)
    builder.add_node("check_report", check_report)
    builder.add_node("repair_report", repair_report)
    builder.add_node("accept_report", accept_report)
    builder.add_node("stop_repairing", stop_repairing)
    builder.add_edge(START, "prepare_report")
    builder.add_edge("prepare_report", "check_report")
    builder.add_conditional_edges("check_report", route_after_check, {
        "accepted": "accept_report",
        "repair": "repair_report",
        "exhausted": "stop_repairing",
    })
    builder.add_edge("repair_report", "check_report")
    builder.add_edge("accept_report", END)
    builder.add_edge("stop_repairing", END)
    return builder.compile()
