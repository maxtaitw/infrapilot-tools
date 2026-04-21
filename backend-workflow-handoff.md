# Backend Workflow Handoff

This document is for Person A / backend integration. It describes only the current implemented behavior of the InfraPilot workflow module.

## Entry Point

Use:

```python
from workflow.engine import build_execution_plan
```

Call `build_execution_plan(data: WorkflowInput)`. It returns an `ExecutionPlan` or raises `ValueError` for validation failures.

JSON examples are available in `integration-examples/`:

- `setup_infra_input.json`
- `setup_infra_output_shape.json`
- `deploy_service_input.json`
- `deploy_service_output_shape.json`

Output examples abbreviate generated Terraform content with placeholder strings.

## Current Input Shape

```python
{
  "intent": "setup_infra | deploy_service | scale_service | stop_service | teardown_service | teardown_infra",
  "entities": dict[str, object],
  "project_state": {
    "project_name": str,
    "region": str | None,
    "infrastructure": dict[str, object],
    "services": dict[str, object],
  },
}
```

## Current Output Shape

```python
{
  "intent": str,
  "steps": [
    {
      "name": str,
      "type": "terraform_apply | terraform_destroy | shell_command",
      "description": str,
      "generated_files": {str: str},
    }
  ],
  "notes": list[str],
  "requires_confirmation": True,
}
```

## `setup_infra` Example

JSON fixtures:

- `integration-examples/setup_infra_input.json`
- `integration-examples/setup_infra_output_shape.json`

Input:

```python
WorkflowInput(
    intent="setup_infra",
    project_state=ProjectState(project_name="demo-project"),
)
```

Output shape:

```python
ExecutionPlan(
    intent="setup_infra",
    steps=[
        PlanStep(
            name="setup_infrastructure",
            type="terraform_apply",
            description="Apply the infrastructure Terraform workflow step.",
            generated_files={
                "infra/main.tf": "<rendered Terraform for networking, ALB, ECS cluster, ECR repository, security groups, IAM role, and outputs>"
            },
        )
    ],
    notes=[
        "Generates one combined Terraform file for setup_infra; Terraform execution remains deferred."
    ],
    requires_confirmation=True,
)
```

Current defaults:

- `region`: `entities["region"]`, then `project_state.region`, then `"us-east-1"`
- `vpc_cidr`: `entities["vpc_cidr"]`, then `"10.0.0.0/16"`

## `deploy_service` Example

JSON fixtures:

- `integration-examples/deploy_service_input.json`
- `integration-examples/deploy_service_output_shape.json`

Input:

```python
WorkflowInput(
    intent="deploy_service",
    entities={
        "service_name": "api",
        "port": 3000,
        "cpu": 256,
        "memory": 512,
        "replicas": 2,
        "image_tag": "v1",
        "environment_variables": {"NODE_ENV": "production"},
    },
    project_state=ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure={
            "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
            "vpc_id": "vpc-123",
            "private_subnet_ids": ["subnet-123", "subnet-456"],
            "alb_listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo/1/2",
            "ecs_task_security_group_id": "sg-123",
            "ecr_url": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo",
        },
    ),
)
```

Output shape:

```python
ExecutionPlan(
    intent="deploy_service",
    steps=[
        PlanStep(name="build_container_image", type="shell_command", generated_files={}),
        PlanStep(name="authenticate_to_ecr", type="shell_command", generated_files={}),
        PlanStep(name="push_container_image", type="shell_command", generated_files={}),
        PlanStep(
            name="apply_service_infrastructure",
            type="terraform_apply",
            description="Apply the minimal service Terraform workflow step.",
            generated_files={
                "service/api/main.tf": "<rendered Terraform for log group, target group, listener rule, task definition, ECS service, and outputs>"
            },
        ),
    ],
    notes=[
        "Generates one minimal service Terraform file for deploy_service; shell command content remains deferred."
    ],
    requires_confirmation=True,
)
```

Important current details:

- The first three `deploy_service` shell steps are placeholders and have empty `generated_files`.
- The fourth step contains the generated service Terraform file.
- If `entities["service_name"]` is missing or blank, the workflow uses `project_state.project_name` and adds an explicit note.
- `environment_variables` may be a flat dictionary.

## Current Validation Failures

`build_execution_plan(...)` raises `ValueError` with semicolon-joined validation messages.

Current validation includes:

- `project_state.project_name` must not be empty
- `entities` must be flat, except `environment_variables` may be a flat dictionary
- service intents require non-empty `project_state.infrastructure`
- `deploy_service` requires these infrastructure keys:
  - `cluster_arn`
  - `vpc_id`
  - `private_subnet_ids`
  - `alb_listener_arn`
  - `ecs_task_security_group_id`
  - `ecr_url`

Example failure:

```text
intent 'deploy_service' requires project_state.infrastructure keys: alb_listener_arn, ecr_url, ecs_task_security_group_id, private_subnet_ids, vpc_id
```

## Non-Goals

The workflow module does not currently do:

- natural-language parsing
- backend routing
- database persistence
- Terraform execution
- Docker execution
- AWS CLI execution
- CLI display or confirmation handling
- real shell command generation
- scale, stop, or teardown service rendering
- multi-step setup-then-deploy planning
