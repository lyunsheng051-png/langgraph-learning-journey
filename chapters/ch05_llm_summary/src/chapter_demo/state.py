from operator import add
from typing import Annotated, Literal, NotRequired, TypedDict


class SummaryState(TypedDict):
    input_path: str
    logs: Annotated[list[str], add]
    document: NotRequired[str]
    raw_response: NotRequired[str]
    summary: NotRequired[dict]
    error: NotRequired[str]
    status: NotRequired[Literal["running", "accepted", "rejected"]]
