"""业务字段相同，只改变 logs 的合并规则。"""

from operator import add
from typing import Annotated, NotRequired, TypedDict


class DocumentFields(TypedDict):
    input_path: str
    text: NotRequired[str]
    character_count: NotRequired[int]
    paragraph_count: NotRequired[int]
    report: NotRequired[str]
    step: NotRequired[str]


class OverwriteState(DocumentFields):
    """普通列表字段：每次更新替换旧值。"""

    logs: list[str]


class AccumulatingState(DocumentFields):
    """为 logs 单独指定列表拼接规则。"""

    logs: Annotated[list[str], add]


DocumentState = OverwriteState | AccumulatingState
