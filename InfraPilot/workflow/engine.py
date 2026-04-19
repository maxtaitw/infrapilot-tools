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
                description="Apply the minimal infrastructure workflow step.",
                generated_files={
                    "infra/main.tf": render_template(
                        "infra/main.tf.j2",
                        resolved_variables,
                    )
                },
            )
        ],
        notes=[
            "Generates one minimal Terraform file for setup_infra; broader infrastructure coverage is deferred."
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
    notes = [
        "Generates one minimal service Terraform file for deploy_service; shell command content remains deferred."
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
                description="Build the service image placeholder step.",
            ),
            PlanStep(
                name="authenticate_to_ecr",
                type="shell_command",
                description="Authenticate to the registry placeholder step.",
            ),
            PlanStep(
                name="push_container_image",
                type="shell_command",
                description="Push the service image placeholder step.",
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
    raw_service_name = data.entities.get("service_name")
    service_name_fallback_used = (
        raw_service_name is None or not str(raw_service_name).strip()
    )
    service_name = (
        data.project_state.project_name
        if service_name_fallback_used
        else str(raw_service_name).strip()
    )

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
        "ecr_url": infrastructure["ecr_url"],
    }


def _build_scale_service_plan(data: WorkflowInput) -> ExecutionPlan:
    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="scale_service",
                type="terraform_apply",
                description="Apply the scaling workflow placeholder step.",
            )
        ],
        notes=["Generated files are deferred in this iteration."],
    )


def _build_stop_service_plan(data: WorkflowInput) -> ExecutionPlan:
    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="stop_service",
                type="terraform_apply",
                description="Apply the stop workflow placeholder step.",
            )
        ],
        notes=["Generated files are deferred in this iteration."],
    )


def _build_teardown_service_plan(data: WorkflowInput) -> ExecutionPlan:
    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="teardown_service",
                type="terraform_destroy",
                description="Destroy the service workflow placeholder step.",
            )
        ],
        notes=["Generated files are deferred in this iteration."],
    )


def _build_teardown_infra_plan(data: WorkflowInput) -> ExecutionPlan:
    return ExecutionPlan(
        intent=data.intent,
        steps=[
            PlanStep(
                name="teardown_infrastructure",
                type="terraform_destroy",
                description="Destroy the infrastructure workflow placeholder step.",
            )
        ],
        notes=["Generated files are deferred in this iteration."],
    )
