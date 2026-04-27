"""Execution plan models produced by the workflow engine."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .inputs import IntentName

StepType = Literal["terraform_apply", "terraform_destroy", "shell_command"]


class CommandInvocation(BaseModel):
    """A structured command description for downstream executors."""

    binary: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    working_directory: str | None = None


class ShellCommandPayload(BaseModel):
    """A shell step payload with an optional command that feeds stdin."""

    command: CommandInvocation
    stdin_source: CommandInvocation | None = None


class PlanStep(BaseModel):
    """A single deterministic step in an execution plan."""

    name: str
    type: StepType
    description: str
    generated_files: dict[str, str] = Field(default_factory=dict)
    execution_payload: ShellCommandPayload | None = None


class ExecutionPlan(BaseModel):
    """A plan returned to downstream backend and CLI layers."""

    intent: IntentName
    steps: list[PlanStep]
    notes: list[str] = Field(default_factory=list)
    requires_confirmation: bool = True
