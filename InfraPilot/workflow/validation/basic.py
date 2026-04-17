"""Minimal validation helpers for workflow engine inputs."""

from __future__ import annotations

from ..schemas.inputs import ProjectState, WorkflowInput

SERVICE_INTENTS_REQUIRING_INFRA = {
    "deploy_service",
    "scale_service",
    "stop_service",
    "teardown_service",
}


def validate_entities_are_flat(entities: dict[str, object]) -> list[str]:
    """Reject nested entity values until concrete schemas are defined."""

    errors: list[str] = []

    for key, value in entities.items():
        if isinstance(value, (dict, list, tuple, set)):
            errors.append(
                f"entities must be a flat dictionary; key '{key}' contains a nested value"
            )

    return errors


def validate_project_state_shape(state: ProjectState) -> list[str]:
    """Apply only basic project-state checks for the current iteration."""

    errors: list[str] = []

    if not state.project_name.strip():
        errors.append("project_state.project_name must not be empty")

    if not isinstance(state.infrastructure, dict):
        errors.append("project_state.infrastructure must be a dictionary")

    if not isinstance(state.services, dict):
        errors.append("project_state.services must be a dictionary")

    return errors


def validate_workflow_input(data: WorkflowInput) -> list[str]:
    """Validate workflow input before the engine builds a plan."""

    errors = []
    errors.extend(validate_entities_are_flat(data.entities))
    errors.extend(validate_project_state_shape(data.project_state))

    if (
        data.intent in SERVICE_INTENTS_REQUIRING_INFRA
        and not data.project_state.infrastructure
    ):
        errors.append(
            f"intent '{data.intent}' requires non-empty project_state.infrastructure"
        )

    return errors
