"""用三个普通 Python 函数搭建顺序工作流。"""

from pathlib import Path
import re

from langgraph.graph import END, START, StateGraph

from chapter_demo.state import DocumentState


MAX_FILE_BYTES = 1024 * 1024


def read_document(state: DocumentState) -> dict[str, str]:
    """读取 UTF-8 TXT；限制读取量，避免一次载入过大的文件。"""
    path = Path(state["input_path"])
    if path.suffix.lower() != ".txt":
        raise ValueError("本章只支持 .txt 文件。")

    with path.open("rb") as source:
        content = source.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("文件超过本章的 1 MiB（1,048,576 字节）上限。")

    return {"text": content.decode("utf-8-sig")}


def analyze_document(state: DocumentState) -> dict[str, int]:
    """字符数排除空白；段落以一个或多个空白行分隔。"""
    text = state["text"]
    paragraphs = [part for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    return {
        "character_count": sum(not character.isspace() for character in text),
        "paragraph_count": len(paragraphs),
    }


def format_report(state: DocumentState) -> dict[str, str]:
    """只格式化结果，不写文件，也不调用模型。"""
    report = "\n".join(
        [
            "文档统计结果",
            f"文件：{Path(state['input_path']).name}",
            f"字符数（不含空白）：{state['character_count']}",
            f"段落数：{state['paragraph_count']}",
        ]
    )
    return {"report": report}


def build_graph():
    """先声明节点和边，再编译为可调用的图。"""
    builder = StateGraph(DocumentState)
    builder.add_node("read_document", read_document)
    builder.add_node("analyze_document", analyze_document)
    builder.add_node("format_report", format_report)

    builder.add_edge(START, "read_document")
    builder.add_edge("read_document", "analyze_document")
    builder.add_edge("analyze_document", "format_report")
    builder.add_edge("format_report", END)

    return builder.compile()


def run_plain(initial_state: DocumentState) -> DocumentState:
    """复用同样的节点，用普通函数调用完成对照实验。"""
    state = initial_state.copy()
    state.update(read_document(state))
    state.update(analyze_document(state))
    state.update(format_report(state))
    return state
