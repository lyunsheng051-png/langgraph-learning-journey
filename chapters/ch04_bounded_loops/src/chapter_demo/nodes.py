from typing import Any

from .state import ReportState

TITLE = "# 出差资料整理"
SOURCE_LINE = "来源：travel_policy.txt"
MISSING_TITLE = "缺少标题"
MISSING_SOURCE = "缺少来源行"


def prepare_report(state: ReportState) -> dict[str, Any]:
    budget = state["max_repairs"]
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError("max_repairs 必须是 0—10 的整数。")
    if state["repair_mode"] not in ("fix", "unchanged"):
        raise ValueError("repair_mode 必须为 fix 或 unchanged。")
    if not isinstance(state["draft"], str):
        raise ValueError("draft 必须是文本。")
    return {
        "repairs": 0, "checks": 0, "issues": [], "status": "running",
        "logs": [f"开始：最多修正 {budget} 次"],
    }


def check_report(state: ReportState) -> dict[str, Any]:
    lines = state["draft"].strip().splitlines()
    issues = []
    if not lines or lines[0] != TITLE:
        issues.append(MISSING_TITLE)
    if not lines or lines[-1] != SOURCE_LINE:
        issues.append(MISSING_SOURCE)
    checks = state["checks"] + 1
    detail = "、".join(issues) if issues else "通过"
    return {"issues": issues, "checks": checks,
            "logs": [f"第 {checks} 次检查：{detail}"]}


def repair_report(state: ReportState) -> dict[str, Any]:
    draft = state["draft"].strip()
    repairs = state["repairs"] + 1
    if state["repair_mode"] == "unchanged":
        action = "保持原文（无效修正实验）"
    elif state["issues"][0] == MISSING_TITLE:
        draft = f"{TITLE}\n\n{draft}"
        action = "补上标题"
    else:
        draft = f"{draft}\n\n{SOURCE_LINE}"
        action = "补上来源行"
    return {"draft": draft, "repairs": repairs,
            "logs": [f"第 {repairs} 次修正：{action}"]}


def accept_report(state: ReportState) -> dict[str, Any]:
    return {"status": "accepted", "logs": ["结束：报告通过检查"]}


def stop_repairing(state: ReportState) -> dict[str, Any]:
    return {"status": "exhausted", "logs": ["结束：修正次数用尽，保留当前草稿"]}
