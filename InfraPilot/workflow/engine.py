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
                description="Apply the service workflow placeholder step.",
            ),
        ],
        notes=["Generated files and command content are deferred in this iteration."],
    )


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
