from dataclasses import dataclass
from importlib.resources import files
from typing import Literal, Protocol

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek
from openai import APIConnectionError, APIStatusError, APITimeoutError

from .settings import Settings

MockCase = Literal["success", "missing-field", "invalid-json", "timeout", "refusal", "truncated"]


class ModelCallError(RuntimeError):
    """对外提供不包含密钥、请求头和服务端原文的失败原因。"""


class SummaryClient(Protocol):
    def invoke(self, messages: list[BaseMessage], *, config: RunnableConfig) -> AIMessage: ...


@dataclass(frozen=True)
class SummaryContext:
    client: SummaryClient


class MockSummaryClient:
    def __init__(self, case: MockCase = "success"):
        self.case = case

    def invoke(self, messages: list[BaseMessage], *, config: RunnableConfig) -> AIMessage:
        fixture_dir = files("chapter_demo").joinpath("fixtures")
        sample = fixture_dir.joinpath("travel_policy.txt").read_text(encoding="utf-8").strip()
        if messages[-1].content != sample:
            raise ModelCallError("mock 固定响应仅适用于包内样例内容；请用样例，或以 real 模式处理自定义资料。")
        if self.case == "timeout":
            raise ModelCallError("模型请求超时；本次未重试。")
        if self.case == "refusal":
            return AIMessage(content="", additional_kwargs={"refusal": "模拟拒答"})
        content = fixture_dir.joinpath(f"{self.case}.json").read_text(encoding="utf-8")
        reason = "length" if self.case == "truncated" else "stop"
        return AIMessage(content=content, response_metadata={"finish_reason": reason})


class DeepSeekSummaryClient:
    def __init__(self, settings: Settings, *, http_client=None):
        # http_client 只用于本地 HTTP 替身测试，正常使用不传入。
        self.model = ChatDeepSeek(
            api_key=settings.api_key,
            model=settings.model,
            api_base="https://api.deepseek.com",
            timeout=30,
            max_retries=0,
            max_tokens=800,
            extra_body={"thinking": {"type": "disabled"}},
            http_client=http_client,
        ).bind(response_format={"type": "json_object"})

    def invoke(self, messages: list[BaseMessage], *, config: RunnableConfig) -> AIMessage:
        try:
            return self.model.invoke(messages, config=config)
        except APITimeoutError:
            raise ModelCallError("模型请求超时；本次未重试。") from None
        except APIConnectionError:
            raise ModelCallError("无法连接 DeepSeek，请检查网络连接；本次未重试。") from None
        except APIStatusError as exc:
            raise ModelCallError(f"DeepSeek 返回 HTTP {exc.status_code}；请检查密钥、额度和模型能力。") from None
