# InfraPilot Workflow Module — Week 2 Status Report

This report summarizes the current state of the workflow module for Week 2. It is a current-state report for teammates, mentor, and reviewers, not a historical log. Update this file whenever the Week 2 workflow/code-generation status changes.

## Week 2 Checklist

- [x] Week 1 input schema exists
- [x] Week 1 output schema exists
- [x] Basic validation exists
- [x] Deterministic intent dispatch exists
- [x] Minimal Jinja2 renderer exists
- [x] Expanded `setup_infra` Terraform generation exists
- [x] Minimal ECS service Terraform template exists
- [x] Minimal service rendering exists for `deploy_service`
- [x] Entity-plus-project-state merge logic exists for `deploy_service`
- [x] `deploy_service` generates one service Terraform file
- [x] `scale_service` generates one service Terraform file
- [x] `stop_service` generates one service Terraform file
- [x] `teardown_service` generates one service Terraform file
- [x] Narrow deploy-service infrastructure-key validation exists
- [x] Tracked workflow contract tests exist
- [x] Backend integration handoff document exists
- [x] Backend integration JSON examples exist
- [x] Terraform validation readiness check rendered current templates locally
- [x] Terraform installed locally for validation
- [x] Rendered Terraform files pass `terraform fmt -check`
- [x] Rendered Terraform files pass `terraform init -backend=false` and `terraform validate`
- [x] `teardown_infra` generates one infrastructure Terraform file for destroy planning
- [x] Review summary exists for teammate and mentor review
- [x] Minimal local dependency file exists
- [ ] Backend integration code is not complete yet
- [ ] Backend source files are not present in this checkout
- [ ] Real AWS account validation for expanded infrastructure is not complete yet

## Current Process

- Upstream should provide structured workflow input, not natural language
- The workflow engine validates the input, dispatches by intent, and returns an execution plan
- The renderer can render templates from `InfraPilot/workflow/templates`
- `setup_infra` currently returns one generated file: `infra/main.tf`
- `deploy_service` currently returns one generated service file: `service/{service_name}/main.tf`
- `scale_service` currently returns one generated service file: `service/{service_name}/main.tf`
- `stop_service` currently returns one generated service file: `service/{service_name}/main.tf`
- `teardown_service` currently returns one generated service file: `service/{service_name}/main.tf`
- `teardown_infra` currently returns one generated file: `infra/main.tf`
- Tracked tests now cover the current `setup_infra`, `deploy_service`, `scale_service`, `stop_service`, `teardown_service`, and `teardown_infra` generation contract
- Backend integration handoff is documented in `backend-workflow-handoff.md`
- Backend integration JSON examples live in `integration-examples/`
- Terraform validation readiness check rendered current templates to `/tmp/infrapilot-template-validation`
- Terraform CLI is installed locally as `v1.14.9`
- Rendered infra, service, scale-service, stop-service, teardown-service, and teardown-infra Terraform all pass `fmt`, `init`, and `validate`
- Review summary is available in `review-summary.md`
- Local dependency setup is tracked in `InfraPilot/requirements.txt`
- Backend integration is blocked in this checkout because no backend app, route, or API package is present
- Remaining Week 2 work should focus on backend integration handoff and real cloud validation planning, not direct execution

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
- `scale_service`, `stop_service`, and `teardown_service` currently require the same infrastructure keys because they reuse the service Terraform template
- `scale_service`, `stop_service`, and `teardown_service` currently require `project_state.services[service_name]`
- `scale_service`, `stop_service`, and `teardown_service` currently require stored service keys `port`, `cpu`, `memory`, `replicas`, and `image_tag`
- `scale_service` requires `entities["replicas"]` as an integer greater than or equal to `1`

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

Current `scale_service` variables from `entities`:

- `service_name`
- `replicas`

Current `scale_service` variables from `project_state.services[service_name]`:

- `port`
- `cpu`
- `memory`
- `replicas`
- `image_tag`
- optional `environment_variables`

Current `stop_service` variables from `entities`:

- `service_name`

Current `stop_service` variables from `project_state.services[service_name]`:

- `port`
- `cpu`
- `memory`
- `replicas`
- `image_tag`
- optional `environment_variables`

Current `teardown_service` variables from `entities`:

- `service_name`

Current `teardown_service` variables from `project_state.services[service_name]`:

- `port`
- `cpu`
- `memory`
- `replicas`
- `image_tag`
- optional `environment_variables`

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
- `scale_service` returns one `terraform_apply` step and generates `service/{service_name}/main.tf`
- `stop_service` returns one `terraform_apply` step and generates `service/{service_name}/main.tf`
- `teardown_service` returns one `terraform_destroy` step and generates `service/{service_name}/main.tf`
- `teardown_infra` returns one `terraform_destroy` step and generates `infra/main.tf`

Current Week 2 output direction:

- `deploy_service` returns one generated service Terraform file
- `scale_service` returns one generated service Terraform file
- `stop_service` returns one generated service Terraform file
- `teardown_service` returns one generated service Terraform file
- service Terraform files use `service/{service_name}/main.tf`
- `generated_files` should remain a dictionary of file path to file content
- execution should remain outside this module

## What Exists Now

Current generated infrastructure file for `setup_infra` and `teardown_infra`: `infra/main.tf`

Currently included:

- Terraform block with AWS provider requirement
- `provider "aws"` using the resolved `region`
- VPC networking
- public and private subnets across two availability zones
- internet gateway
- NAT gateway
- public and private route tables
- ALB with default HTTP listener
- ALB and ECS task security groups
- ECS cluster with Fargate capacity providers and container insights
- ECR repository
- ECS task execution IAM role
- outputs needed by the service template, including `cluster_arn`, `vpc_id`, `private_subnet_ids`, `alb_listener_arn`, `ecs_task_security_group_id`, and `ecr_url`

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
- `scale_service` reuses the same service template with a new desired replica count
- `stop_service` reuses the same service template with `desired_count = 0`
- `teardown_service` reuses the same service template as destroy input

## Week 2 Planned Work

- Coordinate backend integration code so the interpret endpoint can return real execution plans with generated Terraform files
- Bring Person A's backend source files into the shared checkout before wiring the workflow call
- Keep shell-command steps as plan steps only unless command-generation scope is explicitly approved
- Keep Terraform validation command-based unless real execution scope is explicitly approved

## Current Verification

- Tracked tests live in `InfraPilot/tests/workflow/test_engine.py`
- Tests use Python `unittest` and do not add new dependencies
- Current coverage includes `setup_infra` generation, `deploy_service` generation, `scale_service` generation, `stop_service` generation, `teardown_service` generation, `teardown_infra` generation, service-name fallback notes, and missing service validation
- Backend handoff documentation lives in `backend-workflow-handoff.md`
- Backend integration examples live in `integration-examples/`
- Rendered current `setup_infra`, `deploy_service`, `scale_service`, `stop_service`, `teardown_service`, and `teardown_infra` templates into `/tmp/infrapilot-template-validation`
- `scale_service`, `stop_service`, and `teardown_service` were rendered into separate validation directories under `/tmp/infrapilot-template-validation`
- Terraform CLI is installed locally as `v1.14.9`
- Rendered infra, service, scale-service, stop-service, teardown-service, and teardown-infra Terraform passed `terraform fmt -check`
- Rendered infra, service, scale-service, stop-service, teardown-service, and teardown-infra Terraform passed `terraform init -backend=false` and `terraform validate`
- Review summary for teammates and mentor lives in `review-summary.md`
- Local verification dependencies are tracked in `InfraPilot/requirements.txt`

## How To Use It Now

- Use `build_execution_plan(data)` as the workflow entry point
- Use `setup_infra` when you need the one currently generated Terraform file
- Read `plan.steps[0].generated_files["infra/main.tf"]` for current infrastructure Terraform content
- Use `deploy_service` when you need the one currently generated service Terraform file
- Read the Terraform step's `generated_files["service/{service_name}/main.tf"]` for current service Terraform content
- Use `scale_service` when you need a service Terraform file with an updated desired replica count
- Use `stop_service` when you need a service Terraform file with `desired_count = 0`
- Use `teardown_service` when you need a service Terraform file attached to a destroy plan
- Use `teardown_infra` when you need the current infrastructure Terraform file attached to a destroy plan
- Provide the required infrastructure keys when testing `deploy_service`
- Provide stored service state in `project_state.services[service_name]` when testing `scale_service`
- Provide stored service state in `project_state.services[service_name]` when testing `stop_service`
- Provide stored service state in `project_state.services[service_name]` when testing `teardown_service`
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

- Real AWS account validation and hardening for the expanded infrastructure template
- service command generation
- multi-step setup-then-deploy behavior
- direct Terraform, Docker, or AWS execution
- backend routing and persistence
- stricter per-intent schemas and validation
- real AWS testing

## Summary

Current status: Week 1 produced the workflow contract, basic validation, deterministic dispatch, a renderer, and generated `setup_infra` Terraform. Week 2 now has expanded infrastructure generation, generated `deploy_service`, `scale_service`, `stop_service`, `teardown_service`, and `teardown_infra` Terraform inputs, narrow service validation, and review/integration handoff materials while keeping execution outside the workflow module.
