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

EXISTING_SERVICE_INTENTS = {
    "scale_service",
    "stop_service",
    "teardown_service",
}

EXPLICIT_SERVICE_NAME_INTENTS = {
    "stop_service",
    "teardown_service",
}

SCALING_AND_STOP_REQUIRED_STATE_KEYS = {
    "port",
    "cpu",
    "memory",
    "image_tag",
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


def resolve_service_name_for_validation(
    data: WorkflowInput, *, allow_fallback: bool = True
) -> str | None:
    """Resolve service names the same way as the workflow engine."""

    raw_service_name = data.entities.get("service_name")
    if raw_service_name is None or not str(raw_service_name).strip():
        if not allow_fallback:
            return None
        return data.project_state.project_name
    return str(raw_service_name).strip()


def validate_explicit_service_name(data: WorkflowInput) -> list[str]:
    """Require an explicit service name for operational service intents."""

    service_name = resolve_service_name_for_validation(data, allow_fallback=False)
    if service_name is None:
        return [f"intent '{data.intent}' requires entities['service_name']"]
    return []


def validate_existing_service_state(
    data: WorkflowInput, *, required_keys: set[str], allow_fallback: bool = True
) -> list[str]:
    """Require stored service configuration for non-deploy service intents."""

    errors: list[str] = []
    service_name = resolve_service_name_for_validation(
        data,
        allow_fallback=allow_fallback,
    )
    if service_name is None:
        return []

    if service_name not in data.project_state.services:
        return [
            f"intent '{data.intent}' requires project_state.services['{service_name}']"
        ]

    service_state = data.project_state.services[service_name]
    if not isinstance(service_state, dict):
        return [
            f"project_state.services['{service_name}'] must be a dictionary"
        ]

    missing_keys = sorted(
        key
        for key in required_keys
        if key not in service_state or service_state[key] in ("", None)
    )
    if missing_keys:
        errors.append(
            f"intent '{data.intent}' requires project_state.services['{service_name}'] "
            "keys: "
            + ", ".join(missing_keys)
        )

    environment_variables = service_state.get("environment_variables")
    if environment_variables is not None:
        if not isinstance(environment_variables, dict):
            errors.append(
                f"project_state.services['{service_name}'].environment_variables "
                "must be a flat dictionary"
            )
        else:
            for env_key, env_value in environment_variables.items():
                if isinstance(env_value, (dict, list, tuple, set)):
                    errors.append(
                        f"project_state.services['{service_name}']."
                        "environment_variables must be a flat dictionary; "
                        f"key '{env_key}' contains a nested value"
                    )

    return errors


def validate_scale_service_entities(entities: dict[str, object]) -> list[str]:
    """Require a concrete desired replica count for scaling."""

    if "replicas" not in entities:
        return ["intent 'scale_service' requires entities['replicas']"]

    replicas = entities["replicas"]
    if not isinstance(replicas, int) or isinstance(replicas, bool) or replicas < 1:
        return ["intent 'scale_service' requires entities['replicas'] as an integer >= 1"]

    return []


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

    if data.intent in EXISTING_SERVICE_INTENTS:
        errors.extend(validate_deploy_service_infrastructure(data.project_state))
    if data.intent in EXPLICIT_SERVICE_NAME_INTENTS:
        errors.extend(validate_explicit_service_name(data))

    if data.intent == "scale_service":
        errors.extend(
            validate_existing_service_state(
                data,
                required_keys=SCALING_AND_STOP_REQUIRED_STATE_KEYS,
            )
        )
        errors.extend(validate_scale_service_entities(data.entities))

    if data.intent == "stop_service":
        errors.extend(
            validate_existing_service_state(
                data,
                required_keys=SCALING_AND_STOP_REQUIRED_STATE_KEYS,
                allow_fallback=False,
            )
        )

    if data.intent == "teardown_service":
        errors.extend(
            validate_existing_service_state(
                data,
                required_keys=set(),
                allow_fallback=False,
            )
        )

    return errors
