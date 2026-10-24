from pathlib import Path

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from pydantic import ValidationError

from .model_adapter import ModelCallError, SummaryContext
from .prompts import build_messages
from .schemas import DocumentSummary
from .state import SummaryState

MAX_FILE_BYTES = 64 * 1024
MAX_DOCUMENT_CHARS = 4000
MAX_RESPONSE_CHARS = 8000


def read_document(state: SummaryState):
    reset = {"document": "", "raw_response": "", "summary": {}, "error": "", "status": "running"}
    try:
        path = Path(state["input_path"])
        if path.suffix.lower() != ".txt":
            raise ValueError("本章只读取 UTF-8 TXT 文件。")
        # 有界读取，避免仅凭 stat 结果后读取任意长度。
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("输入文件超过 64 KiB。")
        document = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not document:
            raise ValueError("资料为空，未调用模型。")
        if len(document) > MAX_DOCUMENT_CHARS:
            raise ValueError("资料超过 4000 字符，未调用模型；本章不截断或分块。")
    except UnicodeDecodeError:
        return {**reset, "error": "资料不是有效 UTF-8 文本。", "logs": ["读取失败"]}
    except OSError:
        return {**reset, "error": "无法读取文件，请检查路径、文件是否存在及访问权限。", "logs": ["读取失败"]}
    except ValueError as exc:
        return {**reset, "error": str(exc), "logs": ["读取失败"]}
    return {**reset, "document": document, "logs": [f"已读取资料：{len(document)} 字符"]}


def generate_summary(state: SummaryState, config: RunnableConfig, runtime: Runtime[SummaryContext]):
    messages = build_messages(state["document"])
    try:
        response = runtime.context.client.invoke(messages, config=config)
    except ModelCallError as exc:
        return {"error": str(exc), "logs": ["摘要调用失败"]}
    if response.additional_kwargs.get("refusal") or response.response_metadata.get("finish_reason") == "content_filter":
        return {"error": "模型拒绝了本次请求，未生成摘要。", "logs": ["摘要调用未返回可用结果"]}
    if response.response_metadata.get("finish_reason") == "length":
        return {"error": "模型输出达到长度上限，未接受可能被截断的摘要。", "logs": ["摘要输出被截断"]}
    if not isinstance(response.content, str) or not response.content.strip():
        return {"error": "模型没有返回非空文本。", "logs": ["摘要调用未返回可用结果"]}
    if len(response.content) > MAX_RESPONSE_CHARS:
        return {"error": "模型响应超过 8000 字符，未进入结构校验。", "logs": ["摘要输出超限"]}
    return {"raw_response": response.content, "logs": ["已收到摘要响应"]}


def validate_summary(state: SummaryState):
    try:
        result = DocumentSummary.model_validate_json(state["raw_response"])
    except ValidationError as exc:
        # 不回显输入内容，只保留字段位置与错误类型。
        details = []
        for error in exc.errors(include_input=False, include_url=False):
            location = ".".join(map(str, error["loc"])) or "JSON"
            details.append(f"{location} ({error['type']})")
        return {"error": "摘要结构校验失败：" + "；".join(details), "logs": ["摘要结构校验失败"]}
    return {"summary": result.model_dump(), "logs": ["摘要结构校验通过"]}


def accept_summary(state: SummaryState):
    return {"status": "accepted", "logs": ["已接受摘要"]}


def reject_summary(state: SummaryState):
    return {"status": "rejected", "summary": {}, "logs": ["处理结束：未接受摘要"]}
