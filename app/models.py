from typing import Literal

from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    incident: str = Field(min_length=1, max_length=4_000)
    service: str = Field(default="api", min_length=1, max_length=100)


class Evidence(BaseModel):
    source: str
    detail: str


class DiagnoseResponse(BaseModel):
    status: Literal["completed", "needs_attention"]
    summary: str
    recommended_action: str
    evidence: list[Evidence]
    trace: list[str]
