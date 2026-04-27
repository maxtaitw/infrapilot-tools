"""Deterministic workflow engine skeleton for the workflow module."""

from __future__ import annotations

from .rendering.renderer import render_template
from .schemas.inputs import WorkflowInput
from .schemas.plans import ExecutionPlan, PlanStep
from .validation.basic import validate_workflow_input


def build_execution_plan(data: WorkflowInput) -> ExecutionPlan:
    """Validate workflow input and dispatch to an intent-specific builder."""

    errors = validate_workflow_input(data)
    if errors:
        raise ValueError("; ".join(errors))

    if data.intent == "setup_infra":
        return _build_setup_infra_plan(data)
    if data.intent == "deploy_service":
        return _build_deploy_service_plan(data)
    if data.intent == "scale_service":
        return _build_scale_service_plan(data)
    if data.intent == "stop_service":
        return _build_stop_service_plan(data)
    if data.intent == "teardown_service":
        return _build_teardown_service_plan(data)
    if data.intent == "teardown_infra":
        return _build_teardown_infra_plan(data)

    raise ValueError(f"unsupported intent: {data.intent}")


def _build_setup_infra_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_setup_infra_variables(data)

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="setup_infrastructure",
                type="terraform_apply",
                description="Apply the infrastructure Terraform workflow step.",
                generated_files={
                    "infra/main.tf": render_template(
                        "infra/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=[
            "Generates one combined Terraform file for setup_infra; Terraform execution remains deferred."
        ],
    )


def _resolve_setup_infra_variables(data: WorkflowInput) -> dict[str, object]:
    region = (
        data.entities["region"]
        if "region" in data.entities
        else (
            data.project_state.region
            if data.project_state.region is not None
            else "us-east-1"
        )
    )
    vpc_cidr = (
        data.entities["vpc_cidr"]
        if "vpc_cidr" in data.entities
        else "10.0.0.0/16"
    )

    return {
        "project_name": data.project_state.project_name,
        "region": region,
        "vpc_cidr": vpc_cidr,
    }


def _build_deploy_service_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_deploy_service_variables(data)
    service_name = str(resolved_variables["service_name"])
    shell_payloads = _build_deploy_service_shell_payloads(resolved_variables)
    notes = [
        "Generates one minimal service Terraform file for deploy_service plus deterministic shell command payloads; execution remains deferred."
    ]
    if resolved_variables["service_name_fallback_used"]:
        notes.append(
            "deploy_service used project_state.project_name as service_name because entities['service_name'] was not provided."
        )

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="build_container_image",
                type="shell_command",
                description="Build the service container image.",
                execution_payload=shell_payloads["build_container_image"],
            ),
            PlanStep(
                name="authenticate_to_ecr",
                type="shell_command",
                description="Authenticate Docker to Amazon ECR.",
                execution_payload=shell_payloads["authenticate_to_ecr"],
            ),
            PlanStep(
                name="push_container_image",
                type="shell_command",
                description="Push the service container image to Amazon ECR.",
                execution_payload=shell_payloads["push_container_image"],
            ),
            PlanStep(
                name="apply_service_infrastructure",
                type="terraform_apply",
                description="Apply the minimal service Terraform workflow step.",
                generated_files={
                    f"service/{service_name}/main.tf": render_template(
                        "service/main.tf.j2",
                        resolved_variables,
                    )
                },
            ),
        ],
        notes=notes,
    )


def _resolve_deploy_service_variables(data: WorkflowInput) -> dict[str, object]:
    infrastructure = data.project_state.infrastructure
    service_name, service_name_fallback_used = _resolve_service_name(data)

    return {
        "service_name": service_name,
        "service_name_fallback_used": service_name_fallback_used,
        "region": data.entities.get(
            "region",
            data.project_state.region if data.project_state.region else "us-east-1",
        ),
        "port": data.entities.get("port", 3000),
        "cpu": data.entities.get("cpu", 256),
        "memory": data.entities.get("memory", 512),
        "replicas": data.entities.get("replicas", 2),
        "environment_variables": data.entities.get("environment_variables", {}),
        "image_tag": data.entities.get("image_tag", "latest"),
        "cluster_arn": infrastructure["cluster_arn"],
        "vpc_id": infrastructure["vpc_id"],
        "private_subnet_ids": infrastructure["private_subnet_ids"],
        "alb_listener_arn": infrastructure["alb_listener_arn"],
        "ecs_task_security_group_id": infrastructure["ecs_task_security_group_id"],
        "ecs_task_execution_role_arn": infrastructure["ecs_task_execution_role_arn"],
        "ecr_url": infrastructure["ecr_url"],
    }


def _build_deploy_service_shell_payloads(
    variables: dict[str, object],
) -> dict[str, dict[str, object]]:
    image_ref = f"{variables['ecr_url']}:{variables['image_tag']}"
    ecr_registry = str(variables["ecr_url"]).split("/", 1)[0]
    region = str(variables["region"])

    return {
        "build_container_image": {
            "command": {
                "binary": "docker",
                "args": ["build", "-t", image_ref, "."],
                "working_directory": ".",
            }
        },
        "authenticate_to_ecr": {
            "command": {
                "binary": "docker",
                "args": [
                    "login",
                    "--username",
                    "AWS",
                    "--password-stdin",
                    ecr_registry,
                ],
            },
            "stdin_source": {
                "binary": "aws",
                "args": ["ecr", "get-login-password", "--region", region],
            },
        },
        "push_container_image": {
            "command": {
                "binary": "docker",
                "args": ["push", image_ref],
            }
        },
    }


def _resolve_service_name(
    data: WorkflowInput, *, allow_fallback: bool = True
) -> tuple[str, bool]:
    raw_service_name = data.entities.get("service_name")
    service_name_fallback_used = (
        allow_fallback and (raw_service_name is None or not str(raw_service_name).strip())
    )
    service_name = (
        data.project_state.project_name
        if service_name_fallback_used
        else str(raw_service_name).strip()
    )
    return service_name, service_name_fallback_used


def _resolve_existing_service_variables(
    data: WorkflowInput, *, replicas: int, allow_fallback: bool = True
) -> dict[str, object]:
    infrastructure = data.project_state.infrastructure
    service_name, service_name_fallback_used = _resolve_service_name(
        data,
        allow_fallback=allow_fallback,
    )
    service_state = data.project_state.services[service_name]

    return {
        "service_name": service_name,
        "service_name_fallback_used": service_name_fallback_used,
        "region": data.entities.get(
            "region",
            data.project_state.region if data.project_state.region else "us-east-1",
        ),
        "port": service_state["port"],
        "cpu": service_state["cpu"],
        "memory": service_state["memory"],
        "replicas": replicas,
        "environment_variables": service_state.get("environment_variables", {}),
        "image_tag": service_state["image_tag"],
        "cluster_arn": infrastructure["cluster_arn"],
        "vpc_id": infrastructure["vpc_id"],
        "private_subnet_ids": infrastructure["private_subnet_ids"],
        "alb_listener_arn": infrastructure["alb_listener_arn"],
        "ecs_task_security_group_id": infrastructure["ecs_task_security_group_id"],
        "ecs_task_execution_role_arn": infrastructure["ecs_task_execution_role_arn"],
        "ecr_url": infrastructure["ecr_url"],
    }


def _resolve_teardown_service_variables(data: WorkflowInput) -> dict[str, object]:
    infrastructure = data.project_state.infrastructure
    service_name, _ = _resolve_service_name(data, allow_fallback=False)
    service_state = data.project_state.services[service_name]
    used_defaults = any(
        key not in service_state or service_state[key] in ("", None)
        for key in ("port", "cpu", "memory", "replicas", "image_tag")
    )

    return {
        "service_name": service_name,
        "service_name_fallback_used": False,
        "used_service_state_defaults": used_defaults,
        "region": data.entities.get(
            "region",
            data.project_state.region if data.project_state.region else "us-east-1",
        ),
        "port": service_state.get("port", 3000),
        "cpu": service_state.get("cpu", 256),
        "memory": service_state.get("memory", 512),
        "replicas": service_state.get("replicas", 1),
        "environment_variables": service_state.get("environment_variables", {}),
        "image_tag": service_state.get("image_tag", "latest"),
        "cluster_arn": infrastructure["cluster_arn"],
        "vpc_id": infrastructure["vpc_id"],
        "private_subnet_ids": infrastructure["private_subnet_ids"],
        "alb_listener_arn": infrastructure["alb_listener_arn"],
        "ecs_task_security_group_id": infrastructure["ecs_task_security_group_id"],
        "ecs_task_execution_role_arn": infrastructure["ecs_task_execution_role_arn"],
        "ecr_url": infrastructure["ecr_url"],
    }


def _build_scale_service_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_existing_service_variables(
        data,
        replicas=int(data.entities["replicas"]),
    )
    service_name = str(resolved_variables["service_name"])
    notes = [
        "Generates one service Terraform file for scale_service using stored service state; Terraform execution remains deferred."
    ]
    if resolved_variables["service_name_fallback_used"]:
        notes.append(
            "scale_service used project_state.project_name as service_name because entities['service_name'] was not provided."
        )

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="scale_service",
                type="terraform_apply",
                description="Apply the service scaling Terraform workflow step.",
                generated_files={
                    f"service/{service_name}/main.tf": render_template(
                        "service/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=notes,
    )


def _build_stop_service_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_existing_service_variables(
        data,
        replicas=0,
        allow_fallback=False,
    )
    service_name = str(resolved_variables["service_name"])
    notes = [
        "Generates one service Terraform file for stop_service using stored service state with replicas forced to 0; Terraform execution remains deferred."
    ]

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="stop_service",
                type="terraform_apply",
                description="Apply the service stop Terraform workflow step.",
                generated_files={
                    f"service/{service_name}/main.tf": render_template(
                        "service/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=notes,
    )


def _build_teardown_service_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_teardown_service_variables(data)
    service_name = str(resolved_variables["service_name"])
    notes = [
        "Generates one service Terraform file for teardown_service using stored service identity and Terraform-safe defaults for omitted deploy-time fields; Terraform destroy execution remains deferred."
    ]
    if resolved_variables["used_service_state_defaults"]:
        notes.append(
            "teardown_service filled missing stored service fields with deterministic defaults so destroy planning does not fail on stale deploy-time metadata."
        )

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="teardown_service",
                type="terraform_destroy",
                description="Destroy the service Terraform workflow step.",
                generated_files={
                    f"service/{service_name}/main.tf": render_template(
                        "service/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=notes,
    )


def _build_teardown_infra_plan(data: WorkflowInput) -> ExecutionPlan:
    resolved_variables = _resolve_setup_infra_variables(data)

    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="teardown_infrastructure",
                type="terraform_destroy",
                description="Destroy the infrastructure Terraform workflow step.",
                generated_files={
                    "infra/main.tf": render_template(
                        "infra/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=[
            "Generates one combined Terraform file for teardown_infra; Terraform destroy execution remains deferred."
        ],
    )
