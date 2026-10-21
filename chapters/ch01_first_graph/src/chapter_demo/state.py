"""声明本章各节点交换的业务数据。"""

from typing import NotRequired, TypedDict


class DocumentState(TypedDict):
    """输入只需要路径，其余字段随节点执行逐步产生。"""

    input_path: str
    text: NotRequired[str]
    character_count: NotRequired[int]
    paragraph_count: NotRequired[int]
    report: NotRequired[str]
