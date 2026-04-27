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
      "execution_payload": {
        "command": {
          "binary": str,
          "args": list[str],
          "env": dict[str, str],
          "working_directory": str | None,
        },
        "stdin_source": {
          "binary": str,
          "args": list[str],
          "env": dict[str, str],
          "working_directory": str | None,
        } | None,
      } | None,
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
            execution_payload=None,
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
            "ecs_task_execution_role_arn": "arn:aws:iam::123456789012:role/demo-project-ecs-task-execution-role",
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
        PlanStep(
            name="build_container_image",
            type="shell_command",
            generated_files={},
            execution_payload={
                "command": {
                    "binary": "docker",
                    "args": ["build", "-t", "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:v1", "."],
                    "env": {},
                    "working_directory": ".",
                },
                "stdin_source": None,
            },
        ),
        PlanStep(
            name="authenticate_to_ecr",
            type="shell_command",
            generated_files={},
            execution_payload={
                "command": {
                    "binary": "docker",
                    "args": ["login", "--username", "AWS", "--password-stdin", "123456789012.dkr.ecr.us-east-1.amazonaws.com"],
                    "env": {},
                    "working_directory": None,
                },
                "stdin_source": {
                    "binary": "aws",
                    "args": ["ecr", "get-login-password", "--region", "us-east-1"],
                    "env": {},
                    "working_directory": None,
                },
            },
        ),
        PlanStep(
            name="push_container_image",
            type="shell_command",
            generated_files={},
            execution_payload={
                "command": {
                    "binary": "docker",
                    "args": ["push", "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:v1"],
                    "env": {},
                    "working_directory": None,
                },
                "stdin_source": None,
            },
        ),
        PlanStep(
            name="apply_service_infrastructure",
            type="terraform_apply",
            description="Apply the minimal service Terraform workflow step.",
            generated_files={
                "service/api/main.tf": "<rendered Terraform for log group, target group, listener rule, task definition, ECS service, and outputs>"
            },
            execution_payload=None,
        ),
    ],
    notes=[
        "Generates one minimal service Terraform file for deploy_service plus deterministic shell command payloads; execution remains deferred."
    ],
    requires_confirmation=True,
)
```

Important current details:

- The first three `deploy_service` shell steps still have empty `generated_files`, but they now include structured `execution_payload` values.
- The fourth step contains the generated service Terraform file.
- The rendered ECS task definition now includes `execution_role_arn` from `project_state.infrastructure["ecs_task_execution_role_arn"]`.
- If `entities["service_name"]` is missing or blank, the workflow uses `project_state.project_name` and adds an explicit note.
- `environment_variables` may be a flat dictionary.
- `deploy_service` still requires valid infrastructure input. Missing infrastructure remains a validation failure; workflow-core does not auto-plan `setup_infra`.
- Current command-spec assumptions are explicit:
  - Docker build uses `working_directory="."` and build context `.`
  - image references use `{ecr_url}:{image_tag}`
  - ECR login is modeled as a Docker command consuming a structured AWS CLI `stdin_source`
- Executors remain responsible for process execution, credential sourcing, logging, retries, and workspace setup.

## `scale_service` Example

Input:

```python
WorkflowInput(
    intent="scale_service",
    entities={"service_name": "api", "replicas": 4},
    project_state=ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure={
            "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
            "vpc_id": "vpc-123",
            "private_subnet_ids": ["subnet-123", "subnet-456"],
            "alb_listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo/1/2",
            "ecs_task_security_group_id": "sg-123",
            "ecs_task_execution_role_arn": "arn:aws:iam::123456789012:role/demo-project-ecs-task-execution-role",
            "ecr_url": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo",
        },
        services={
            "api": {
                "port": 3000,
                "cpu": 256,
                "memory": 512,
                "replicas": 2,
                "image_tag": "v1",
                "environment_variables": {"NODE_ENV": "production"},
            }
        },
    ),
)
```

Output shape:

```python
ExecutionPlan(
    intent="scale_service",
    steps=[
        PlanStep(
            name="scale_service",
            type="terraform_apply",
            description="Apply the service scaling Terraform workflow step.",
            generated_files={
                "service/api/main.tf": "<rendered Terraform for the existing service with desired_count set to 4>"
            },
            execution_payload=None,
        )
    ],
    notes=[
        "Generates one service Terraform file for scale_service using stored service state; Terraform execution remains deferred."
    ],
    requires_confirmation=True,
)
```

Important current details:

- `scale_service` reuses `project_state.services[service_name]` for stored service configuration.
- `entities["replicas"]` is required and must be an integer greater than or equal to `1`.
- The optional `execution_payload` field currently remains `None`.
- The generated file path matches `deploy_service`: `service/{service_name}/main.tf`.

## `stop_service` Example

Input:

```python
WorkflowInput(
    intent="stop_service",
    entities={"service_name": "api"},
    project_state=ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure={
            "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
            "vpc_id": "vpc-123",
            "private_subnet_ids": ["subnet-123", "subnet-456"],
            "alb_listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo/1/2",
            "ecs_task_security_group_id": "sg-123",
            "ecs_task_execution_role_arn": "arn:aws:iam::123456789012:role/demo-project-ecs-task-execution-role",
            "ecr_url": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo",
        },
        services={
            "api": {
                "port": 3000,
                "cpu": 256,
                "memory": 512,
                "replicas": 2,
                "image_tag": "v1",
                "environment_variables": {"NODE_ENV": "production"},
            }
        },
    ),
)
```

Output shape:

```python
ExecutionPlan(
    intent="stop_service",
    steps=[
        PlanStep(
            name="stop_service",
            type="terraform_apply",
            description="Apply the service stop Terraform workflow step.",
            generated_files={
                "service/api/main.tf": "<rendered Terraform for the existing service with desired_count forced to 0>"
            },
            execution_payload=None,
        )
    ],
    notes=[
        "Generates one service Terraform file for stop_service using stored service state with replicas forced to 0; Terraform execution remains deferred."
    ],
    requires_confirmation=True,
)
```

Important current details:

- `stop_service` reuses `project_state.services[service_name]` for stored service configuration.
- `stop_service` does not require `entities["replicas"]`; it always renders `desired_count = 0`.
- `stop_service` requires explicit `entities["service_name"]`; it does not fall back to `project_state.project_name`.
- The optional `execution_payload` field currently remains `None`.
- The generated file path matches `deploy_service` and `scale_service`: `service/{service_name}/main.tf`.

## `teardown_service` Example

Input:

```python
WorkflowInput(
    intent="teardown_service",
    entities={"service_name": "api"},
    project_state=ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure={
            "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
            "vpc_id": "vpc-123",
            "private_subnet_ids": ["subnet-123", "subnet-456"],
            "alb_listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo/1/2",
            "ecs_task_security_group_id": "sg-123",
            "ecs_task_execution_role_arn": "arn:aws:iam::123456789012:role/demo-project-ecs-task-execution-role",
            "ecr_url": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo",
        },
        services={
            "api": {
                "port": 3000,
                "cpu": 256,
                "memory": 512,
                "replicas": 2,
                "image_tag": "v1",
                "environment_variables": {"NODE_ENV": "production"},
            }
        },
    ),
)
```

Output shape:

```python
ExecutionPlan(
    intent="teardown_service",
    steps=[
        PlanStep(
            name="teardown_service",
            type="terraform_destroy",
            description="Destroy the service Terraform workflow step.",
            generated_files={
                "service/api/main.tf": "<rendered Terraform for the existing service resources to be destroyed>"
            },
            execution_payload=None,
        )
    ],
    notes=[
        "Generates one service Terraform file for teardown_service using stored service state; Terraform destroy execution remains deferred."
    ],
    requires_confirmation=True,
)
```

Important current details:

- `teardown_service` requires explicit `entities["service_name"]`; it does not fall back to `project_state.project_name`.
- `teardown_service` currently reuses the same service Terraform template as deploy/scale/stop.
- `teardown_service` only requires `project_state.services[service_name]` to exist as a dictionary. Missing deploy-time fields are filled with deterministic defaults so destroy planning does not fail on stale stored metadata.
- The optional `execution_payload` field currently remains `None`.
- The generated file path matches the other service intents: `service/{service_name}/main.tf`.

## Current Validation Failures

`build_execution_plan(...)` raises `ValueError` with semicolon-joined validation messages.

Current validation includes:

- `project_state.project_name` must not be empty
- `entities` must be flat, except `environment_variables` may be a flat dictionary
- service intents require non-empty `project_state.infrastructure`
- `teardown_infra` requires empty `project_state.services`
- `deploy_service` requires these infrastructure keys:
  - `cluster_arn`
  - `vpc_id`
  - `private_subnet_ids`
  - `alb_listener_arn`
  - `ecs_task_security_group_id`
  - `ecs_task_execution_role_arn`
  - `ecr_url`
- `scale_service`, `stop_service`, and `teardown_service` currently require the same infrastructure keys because they reuse the service Terraform template
- `scale_service`, `stop_service`, and `teardown_service` require `project_state.services[service_name]`
- `stop_service` and `teardown_service` require explicit `entities["service_name"]`
- `scale_service` requires `entities["replicas"]`
- workflow-core still plans one intent at a time; multi-step setup-then-deploy orchestration is expected to happen upstream

Example failure:

```text
intent 'deploy_service' requires project_state.infrastructure keys: alb_listener_arn, ecs_task_execution_role_arn, ecr_url, ecs_task_security_group_id, private_subnet_ids, vpc_id
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
- multi-intent orchestration inside workflow-core
