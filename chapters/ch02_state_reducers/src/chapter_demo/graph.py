"""三个节点各返回一条日志，用两份 schema 对照更新规则。"""

from pathlib import Path
import re
from typing import Literal

from langgraph.graph import END, START, StateGraph

from chapter_demo.state import AccumulatingState, DocumentState, OverwriteState


LogMode = Literal["append", "overwrite"]
MAX_FILE_BYTES = 1024 * 1024


def read_document(state: DocumentState) -> dict:
    path = Path(state["input_path"])
    if path.suffix.lower() != ".txt":
        raise ValueError("本章只支持 .txt 文件。")
    with path.open("rb") as source:
        content = source.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("文件超过本章的 1 MiB（1,048,576 字节）上限。")
    return {
        "text": content.decode("utf-8-sig"),
        "step": "读取完成",
        "logs": [f"已读取：{path.name}"],
    }


def analyze_document(state: DocumentState) -> dict:
    text = state["text"]
    paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    character_count = sum(not character.isspace() for character in text)
    paragraph_count = len(paragraphs)
    return {
        "character_count": character_count,
        "paragraph_count": paragraph_count,
        "step": "统计完成",
        "logs": [f"已统计：{character_count} 个非空白字符，{paragraph_count} 个段落"],
    }


def format_report(state: DocumentState) -> dict:
    report = "\n".join(
        [
            "文档统计结果",
            f"文件：{Path(state['input_path']).name}",
            f"字符数（不含空白）：{state['character_count']}",
            f"段落数：{state['paragraph_count']}",
        ]
    )
    return {
        "report": report,
        "step": "整理完成",
        "logs": ["已整理统计报告"],
    }


def build_graph(log_mode: LogMode = "append"):
    if log_mode == "append":
        schema = AccumulatingState
    elif log_mode == "overwrite":
        schema = OverwriteState
    else:
        raise ValueError("日志规则只支持 append 或 overwrite。")

    builder = StateGraph(schema)
    builder.add_node("read_document", read_document)
    builder.add_node("analyze_document", analyze_document)
    builder.add_node("format_report", format_report)
    builder.add_edge(START, "read_document")
    builder.add_edge("read_document", "analyze_document")
    builder.add_edge("analyze_document", "format_report")
    builder.add_edge("format_report", END)
    return builder.compile()
