"""Input models for the workflow module boundary."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

IntentName = Literal[
    "setup_infra",
    "deploy_service",
    "scale_service",
    "stop_service",
    "teardown_service",
    "teardown_infra",
]


class ProjectState(BaseModel):
    """Minimal project state required to plan workflows."""

    project_name: str
    region: str | None = None
    infrastructure: dict[str, object] = Field(default_factory=dict)
    services: dict[str, object] = Field(default_factory=dict)


class WorkflowInput(BaseModel):
    """Structured input consumed by the workflow engine."""

    intent: IntentName
    entities: dict[str, object] = Field(default_factory=dict)
    project_state: ProjectState
