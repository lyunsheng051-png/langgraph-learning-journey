"""条件边只做选择，解析节点只返回文本或明确错误。"""

from pathlib import Path
from typing import Callable, Literal

from langgraph.graph import END, START, StateGraph

from chapter_demo.extractors import (
    ExtractionError, MAX_FILE_BYTES, extract_docx, extract_pdf, extract_txt,
)
from chapter_demo.state import DocumentState, TextSection


def prepare_input(state: DocumentState) -> dict:
    path = Path(state["input_path"])
    update = {"file_type": path.suffix.lower().lstrip("."), "logs": [f"已检查：{path.name}"]}
    try:
        if not path.is_file():
            update["error"] = "文件不存在或路径不是文件。"
        elif path.stat().st_size > MAX_FILE_BYTES:
            update["error"] = "文件超过本章的 1 MiB 上限。"
    except OSError:
        update["error"] = "无法访问文件，请检查路径与读取权限。"
    return update


def route_by_type(state: DocumentState) -> Literal["txt", "docx", "pdf", "reject"]:
    if state.get("error"):
        return "reject"
    file_type = state["file_type"]
    if file_type in ("txt", "docx", "pdf"):
        return file_type
    return "reject"


def extract_with(state: DocumentState, extractor: Callable[[Path], list[TextSection]], label: str) -> dict:
    try:
        sections = extractor(Path(state["input_path"]))
        if not sections:
            raise ExtractionError("未提取到可处理文本；本章不提供 OCR，也不处理 DOCX 表格或图片。")
    except (ExtractionError, OSError) as error:
        return {"error": str(error), "logs": [f"提取失败（{label}）：{error}"]}
    return {"sections": sections, "logs": [f"已提取（{label}）：{len(sections)} 个文本片段"]}


def extract_txt_node(state: DocumentState) -> dict:
    return extract_with(state, extract_txt, "TXT")


def extract_docx_node(state: DocumentState) -> dict:
    return extract_with(state, extract_docx, "DOCX")


def extract_pdf_node(state: DocumentState) -> dict:
    return extract_with(state, extract_pdf, "PDF")


def route_after_extract(state: DocumentState) -> Literal["ready", "reject"]:
    return "reject" if state.get("error") else "ready"


def analyze_document(state: DocumentState) -> dict:
    characters = sum(not char.isspace() for section in state["sections"] for char in section["text"])
    return {
        "character_count": characters,
        "section_count": len(state["sections"]),
        "logs": [f"已统计：{characters} 个非空白字符"],
    }


def format_report(state: DocumentState) -> dict:
    report = "\n".join([
        "文档提取结果",
        f"文件：{Path(state['input_path']).name}",
        f"提取方式：{state['file_type'].upper()}",
        f"字符数（不含空白）：{state['character_count']}",
        f"文本片段数：{state['section_count']}",
        "来源位置：" + "、".join(section["location"] for section in state["sections"]),
    ])
    return {"report": report, "status": "ok", "logs": ["已整理提取结果"]}


def reject_input(state: DocumentState) -> dict:
    error = state.get("error") or f"不支持文件类型：{state.get('file_type') or '无扩展名'}；仅支持 TXT、DOCX、PDF。"
    report = f"文档处理失败\n文件：{Path(state['input_path']).name}\n原因：{error}"
    return {"error": error, "status": "error", "report": report, "logs": ["已结束：本次输入无法处理"]}


def build_graph():
    builder = StateGraph(DocumentState)
    builder.add_node("prepare_input", prepare_input)
    builder.add_node("extract_txt", extract_txt_node)
    builder.add_node("extract_docx", extract_docx_node)
    builder.add_node("extract_pdf", extract_pdf_node)
    builder.add_node("analyze_document", analyze_document)
    builder.add_node("format_report", format_report)
    builder.add_node("reject_input", reject_input)

    builder.add_edge(START, "prepare_input")
    builder.add_conditional_edges("prepare_input", route_by_type, {
        "txt": "extract_txt", "docx": "extract_docx", "pdf": "extract_pdf", "reject": "reject_input",
    })
    for name in ("extract_txt", "extract_docx", "extract_pdf"):
        builder.add_conditional_edges(name, route_after_extract, {
            "ready": "analyze_document", "reject": "reject_input",
        })
    builder.add_edge("analyze_document", "format_report")
    builder.add_edge("format_report", END)
    builder.add_edge("reject_input", END)
    return builder.compile()
