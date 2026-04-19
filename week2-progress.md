# InfraPilot Workflow Module — Week 2 Status Report

This report summarizes the current state of the workflow module for Week 2. It is a current-state report for teammates, mentor, and reviewers, not a historical log. Update this file whenever the Week 2 workflow/code-generation status changes.

## Week 2 Checklist

- [x] Week 1 input schema exists
- [x] Week 1 output schema exists
- [x] Basic validation exists
- [x] Deterministic intent dispatch exists
- [x] Minimal Jinja2 renderer exists
- [x] Minimal `setup_infra` Terraform generation exists
- [x] Minimal ECS service Terraform template exists
- [x] Minimal service rendering exists for `deploy_service`
- [x] Entity-plus-project-state merge logic exists for `deploy_service`
- [x] `deploy_service` generates one service Terraform file
- [x] Narrow deploy-service infrastructure-key validation exists
- [ ] Backend integration handoff is not complete yet
- [ ] Terraform validation for full infra and service templates is not complete yet
- [ ] Broader infrastructure coverage from the original Week 1 plan is not complete yet

## Current Process

- Upstream should provide structured workflow input, not natural language
- The workflow engine validates the input, dispatches by intent, and returns an execution plan
- The renderer can render templates from `InfraPilot/workflow/templates`
- `setup_infra` currently returns one generated file: `infra/main.tf`
- `deploy_service` currently returns one generated service file: `service/{service_name}/main.tf`
- Scale, stop, teardown service, and teardown infrastructure still return deterministic placeholder plans without real generated files
- Remaining Week 2 work should focus on integration handoff and validation readiness, not direct execution

## Current Input Contract

Use `WorkflowInput` with:

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

Current validation rules:

- `project_state.project_name` must not be empty
- `project_state.infrastructure` must be a dictionary
- `project_state.services` must be a dictionary
- `entities` must be flat; nested `dict`, `list`, `tuple`, and `set` values are rejected except for `environment_variables`
- `entities.environment_variables` may be a flat dictionary for `deploy_service`
- `deploy_service`, `scale_service`, `stop_service`, and `teardown_service` currently require non-empty `project_state.infrastructure`
- `deploy_service` requires `cluster_arn`, `vpc_id`, `private_subnet_ids`, `alb_listener_arn`, `ecs_task_security_group_id`, and `ecr_url` in `project_state.infrastructure`

Current `setup_infra` variables:

- `project_name` comes from `project_state.project_name`
- `region` uses `entities["region"]`, then `project_state.region`, then `"us-east-1"`
- `vpc_cidr` uses `entities["vpc_cidr"]`, then `"10.0.0.0/16"`

Current `deploy_service` variables from `entities`:

- `service_name`
- `port`
- `cpu`
- `memory`
- `replicas`
- `environment_variables`
- `image_tag`

Current `deploy_service` variables from `project_state.infrastructure`:

- `cluster_arn`
- `vpc_id`
- `private_subnet_ids`
- `alb_listener_arn`
- `ecs_task_security_group_id`
- `ecr_url`

## Current Output Contract

The engine returns `ExecutionPlan`:

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

Current behavior by intent:

- `setup_infra` returns one `terraform_apply` step and generates `infra/main.tf`
- `deploy_service` returns four steps; the three shell steps remain placeholders and the Terraform step generates `service/{service_name}/main.tf`
- `scale_service` returns one placeholder `terraform_apply` step
- `stop_service` returns one placeholder `terraform_apply` step
- `teardown_service` returns one placeholder `terraform_destroy` step
- `teardown_infra` returns one placeholder `terraform_destroy` step

Current Week 2 output direction:

- `deploy_service` returns one generated service Terraform file
- service Terraform files use `service/{service_name}/main.tf`
- `generated_files` should remain a dictionary of file path to file content
- execution should remain outside this module

## What Exists Now

Current generated infrastructure file: `infra/main.tf`

Currently included:

- Terraform block with AWS provider requirement
- `provider "aws"` using the resolved `region`
- `aws_vpc`
- `aws_ecs_cluster`
- `aws_ecr_repository`
- outputs for `vpc_id`, `ecs_cluster_name`, and `ecr_repository_url`

Current renderer:

- Function: `render_template(template_name: str, variables: dict[str, object]) -> str`
- Template root: `InfraPilot/workflow/templates`
- Current real templates: `infra/main.tf.j2` and `service/main.tf.j2`

Current generated service file: `service/{service_name}/main.tf`

Currently included:

- CloudWatch log group
- ALB target group
- ALB listener rule
- ECS task definition
- ECS service
- outputs for service name, target group ARN, and log group name

## Week 2 Planned Work

- Complete backend integration handoff so the interpret endpoint can return real execution plans with generated Terraform files
- Keep shell-command steps as plan steps only unless command-generation scope is explicitly approved
- Run Terraform validation when the full template shape is ready and Terraform is available

## How To Use It Now

- Use `build_execution_plan(data)` as the workflow entry point
- Use `setup_infra` when you need the one currently generated Terraform file
- Read `plan.steps[0].generated_files["infra/main.tf"]` for current infrastructure Terraform content
- Use `deploy_service` when you need the one currently generated service Terraform file
- Read the Terraform step's `generated_files["service/{service_name}/main.tf"]` for current service Terraform content
- Provide the required infrastructure keys when testing `deploy_service`
- Use scale, stop, and teardown intents only to inspect placeholder plan structure for now
- Do not expect this module to run Terraform, Docker, AWS CLI, or backend calls

Minimal current `setup_infra` example:

```python
from workflow.engine import build_execution_plan
from workflow.schemas.inputs import ProjectState, WorkflowInput

plan = build_execution_plan(
    WorkflowInput(
        intent="setup_infra",
        project_state=ProjectState(project_name="demo-project"),
    )
)
```

Minimal current `deploy_service` example:

```python
from workflow.engine import build_execution_plan
from workflow.schemas.inputs import ProjectState, WorkflowInput

plan = build_execution_plan(
    WorkflowInput(
        intent="deploy_service",
        entities={"service_name": "api", "port": 3000},
        project_state=ProjectState(
            project_name="demo-project",
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
)
```

## Deferred After Current State

- full infrastructure template coverage from the original Week 1 plan
- service command generation
- multi-step setup-then-deploy behavior
- scale, stop, and teardown service rendering
- direct Terraform, Docker, or AWS execution
- backend routing and persistence
- stricter per-intent schemas and validation
- real AWS testing

## Summary

Current status: Week 1 produced the workflow contract, basic validation, deterministic dispatch, a minimal renderer, and one generated `setup_infra` Terraform file. Week 2 now adds one generated `deploy_service` Terraform file and narrow deploy infrastructure validation while keeping execution outside the workflow module.
