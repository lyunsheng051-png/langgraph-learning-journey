from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SummaryText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
KeyPoint = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class DocumentSummary(BaseModel):
    """短文档的摘要；这里只校验结构和长度。"""

    model_config = ConfigDict(extra="forbid", strict=True)
    summary: SummaryText = Field(description="用中文概括资料，1—200 字符，不补充原文以外的信息")
    key_points: list[KeyPoint] = Field(min_length=1, max_length=5, description="1—5 条关键事项，每条 1—100 字符")
