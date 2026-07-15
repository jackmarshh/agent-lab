from typing import Literal

from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    incident: str = Field(min_length=1, max_length=4_000)
    service: str = Field(default="api", min_length=1, max_length=100)
    conversation_id: str = Field(default="default-session")  # 新增：会话 ID


class Evidence(BaseModel):
    source: str
    detail: str


class DiagnoseResponse(BaseModel):
    status: Literal["completed", "needs_attention"]
    summary: str
    recommended_action: str
    evidence: list[Evidence]
    trace: list[str]
    metadata: dict = Field(default_factory=dict)  # 新增：元数据，用于存储 Token 消耗等统计信息
