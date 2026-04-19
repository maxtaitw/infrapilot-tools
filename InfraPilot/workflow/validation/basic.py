"""Minimal validation helpers for workflow engine inputs."""

from __future__ import annotations

from ..schemas.inputs import ProjectState, WorkflowInput

SERVICE_INTENTS_REQUIRING_INFRA = {
    "deploy_service",
    "scale_service",
    "stop_service",
    "teardown_service",
}

DEPLOY_SERVICE_REQUIRED_INFRASTRUCTURE_KEYS = {
    "cluster_arn",
    "vpc_id",
    "private_subnet_ids",
    "alb_listener_arn",
    "ecs_task_security_group_id",
    "ecr_url",
}


def validate_entities_are_flat(entities: dict[str, object]) -> list[str]:
    """Reject nested entity values until concrete schemas are defined."""

    errors: list[str] = []

    for key, value in entities.items():
        if key == "environment_variables" and isinstance(value, dict):
            for env_key, env_value in value.items():
                if isinstance(env_value, (dict, list, tuple, set)):
                    errors.append(
                        "entities.environment_variables must be a flat dictionary; "
                        f"key '{env_key}' contains a nested value"
                    )
            continue

        if isinstance(value, (dict, list, tuple, set)):
            errors.append(
                f"entities must be a flat dictionary; key '{key}' contains a nested value"
            )

    return errors


def validate_environment_variables_shape(entities: dict[str, object]) -> list[str]:
    """Allow only a flat dictionary for service environment variables."""

    if "environment_variables" not in entities:
        return []

    if not isinstance(entities["environment_variables"], dict):
        return ["entities.environment_variables must be a flat dictionary"]

    return []


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


def validate_deploy_service_infrastructure(state: ProjectState) -> list[str]:
    """Require only the infrastructure fields needed to render service Terraform."""

    errors: list[str] = []

    if not state.infrastructure:
        return errors

    missing_keys = sorted(
        key
        for key in DEPLOY_SERVICE_REQUIRED_INFRASTRUCTURE_KEYS
        if key not in state.infrastructure or not state.infrastructure[key]
    )
    if missing_keys:
        errors.append(
            "intent 'deploy_service' requires project_state.infrastructure keys: "
            + ", ".join(missing_keys)
        )

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

    if data.intent == "deploy_service":
        errors.extend(validate_environment_variables_shape(data.entities))
        errors.extend(validate_deploy_service_infrastructure(data.project_state))

    return errors
