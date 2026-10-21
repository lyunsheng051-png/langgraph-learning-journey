"""不同解析节点交回同一种文本片段结构。"""

from operator import add
from typing import Annotated, Literal, NotRequired, TypedDict


class TextSection(TypedDict):
    location: str
    text: str


class DocumentState(TypedDict):
    input_path: str
    logs: Annotated[list[str], add]
    file_type: NotRequired[str]
    sections: NotRequired[list[TextSection]]
    error: NotRequired[str]
    character_count: NotRequired[int]
    section_count: NotRequired[int]
    report: NotRequired[str]
    status: NotRequired[Literal["ok", "error"]]
