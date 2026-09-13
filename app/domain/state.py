from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    execution_id: str = "hackathon-run"
    data: dict[str, Any] = Field(default_factory=dict)
