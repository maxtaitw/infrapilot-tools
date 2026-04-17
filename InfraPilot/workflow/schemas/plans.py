"""Execution plan models produced by the workflow engine."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .inputs import IntentName

StepType = Literal["terraform_apply", "terraform_destroy", "shell_command"]


class PlanStep(BaseModel):
    """A single deterministic step in an execution plan."""

    name: str
    type: StepType
    description: str
    generated_files: dict[str, str] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """A plan returned to downstream backend and CLI layers."""

    intent: IntentName
    steps: list[PlanStep]
    notes: list[str] = Field(default_factory=list)
    requires_confirmation: bool = True
