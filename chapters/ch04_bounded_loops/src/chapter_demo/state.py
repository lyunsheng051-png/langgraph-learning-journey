from operator import add
from typing import Annotated, Literal, NotRequired, TypedDict


class ReportState(TypedDict):
    draft: str
    max_repairs: int
    repair_mode: Literal["fix", "unchanged"]
    repairs: NotRequired[int]
    checks: NotRequired[int]
    issues: NotRequired[list[str]]
    status: NotRequired[Literal["running", "accepted", "exhausted"]]
    logs: Annotated[list[str], add]
