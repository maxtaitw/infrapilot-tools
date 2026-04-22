# B-C Contract

This document defines the current boundary between Person B's intent/entity layer and Person C's workflow module. It reflects current implemented behavior only.

## Responsibility Split

Person B / upstream layer owns:

- natural-language interpretation
- intent selection
- entity extraction
- passing structured workflow input

Person C / workflow module owns:

- validating structured workflow input
- combining entities with project state where currently implemented
- returning deterministic execution plans
- returning generated Terraform file contents for currently supported generation paths

## Current Implemented Behavior

Supported intents:

- `setup_infra`
- `deploy_service`
- `scale_service`
- `stop_service`
- `teardown_service`
- `teardown_infra`

Currently generated files:

- `setup_infra` generates `infra/main.tf`
- `deploy_service` generates `service/{service_name}/main.tf`
- `teardown_infra` generates `infra/main.tf`
- `scale_service`, `stop_service`, and `teardown_service` still return placeholder plan steps only

Current step types:

- `terraform_apply`
- `terraform_destroy`
- `shell_command`

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

## Current Entity Expectations

General rule:

- `entities` should be flat
- `environment_variables` may be a flat dictionary for `deploy_service`

`setup_infra` currently uses:

- `region`
- `vpc_cidr`

`deploy_service` currently uses:

- `service_name`
- `port`
- `cpu`
- `memory`
- `replicas`
- `environment_variables`
- `image_tag`

`teardown_infra` uses the same currently supported entities as `setup_infra`.

`scale_service`, `stop_service`, and `teardown_service` do not generate real files yet, so their final entity contracts are still open.

## Current Workflow Output Shape

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

`generated_files` is now real for `setup_infra`, `teardown_infra`, and the Terraform step of `deploy_service`.

## `setup_infra` Behavior

Current plan:

- one `terraform_apply` step named `setup_infrastructure`
- generated file: `infra/main.tf`
- current Terraform coverage includes AWS provider, VPC networking, public and private subnets, internet gateway, NAT gateway, route tables, ALB, security groups, ECS cluster, ECR repository, IAM execution role, and outputs needed by the service template

Current variable priority:

- `project_name`: `project_state.project_name`
- `region`: `entities["region"]`, then `project_state.region`, then `"us-east-1"`
- `vpc_cidr`: `entities["vpc_cidr"]`, then `"10.0.0.0/16"`

## `teardown_infra` Behavior

Current plan:

- one `terraform_destroy` step named `teardown_infrastructure`
- generated file: `infra/main.tf`
- uses the same infrastructure template and variable priority as `setup_infra`
- prepares Terraform destroy input only; Terraform execution remains outside the workflow module

## `deploy_service` Behavior

Current plan:

- `build_container_image` shell placeholder step
- `authenticate_to_ecr` shell placeholder step
- `push_container_image` shell placeholder step
- `apply_service_infrastructure` Terraform step with generated service Terraform

Generated file:

- `service/{service_name}/main.tf`

Current Terraform coverage is minimal:

- CloudWatch log group
- ALB target group
- ALB listener rule
- ECS task definition
- ECS service
- service-related outputs

Current `service_name` rule:

- use `entities["service_name"]` when provided and non-empty
- otherwise use `project_state.project_name`
- when fallback is used, the plan includes an explicit note

Current required `project_state.infrastructure` keys for `deploy_service`:

- `cluster_arn`
- `vpc_id`
- `private_subnet_ids`
- `alb_listener_arn`
- `ecs_task_security_group_id`
- `ecr_url`

## Current Validation Behavior

The workflow entry point raises `ValueError` when validation fails.

Current validation rules:

- `project_state.project_name` must not be empty
- `project_state.infrastructure` must be a dictionary
- `project_state.services` must be a dictionary
- `entities` must be flat, except `environment_variables` may be a flat dictionary
- `deploy_service`, `scale_service`, `stop_service`, and `teardown_service` require non-empty `project_state.infrastructure`
- `deploy_service` requires the six infrastructure keys listed above

Validation messages are joined into one `ValueError` string.

## Open B-C Discussion Items

- Decide how Person B should signal multi-step setup-then-deploy behavior.
- Decide final defaults and required fields for `scale_service`, `stop_service`, and `teardown_service`.
- Decide whether Person B or Person C owns stricter normalization for CPU, memory, replicas, ports, and service names.
- Confirm that `environment_variables` should remain a flat dictionary.
- Decide whether missing service names for non-deploy service intents should fall back to `project_state.project_name` or produce clarification/validation errors.
