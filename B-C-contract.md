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
- `scale_service` generates `service/{service_name}/main.tf`
- `stop_service` generates `service/{service_name}/main.tf`
- `teardown_service` generates `service/{service_name}/main.tf`
- `teardown_infra` generates `infra/main.tf`

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

`scale_service` currently uses:

- `service_name`
- `replicas`

`stop_service` currently uses:

- `service_name`

`teardown_service` currently uses:

- `service_name`

`teardown_infra` uses the same currently supported entities as `setup_infra`.

`scale_service` currently requires `project_state.services[service_name]` with:

- `port`
- `cpu`
- `memory`
- `image_tag`
- optional `environment_variables` as a flat dictionary

`stop_service` currently requires the same stored service-state contract as `scale_service`.

`teardown_service` currently requires only that `project_state.services[service_name]` exists as a dictionary. Missing deploy-time fields currently fall back to deterministic defaults during destroy planning.

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

`generated_files` is now real for `setup_infra`, `teardown_infra`, `scale_service`, `stop_service`, `teardown_service`, and the Terraform step of `deploy_service`.
`execution_payload` is optional. It is currently populated for the three `deploy_service` shell steps and remains `None` for Terraform-only steps.

Current shell payload shape:

- `command.binary`
- `command.args`
- optional `command.env`
- optional `command.working_directory`
- optional `stdin_source` with the same nested command shape

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
- rejects destroy planning when `project_state.services` is non-empty
- prepares Terraform destroy input only; Terraform execution remains outside the workflow module

## `deploy_service` Behavior

Current plan:

- `build_container_image` shell step with structured command payload
- `authenticate_to_ecr` shell step with structured command payload
- `push_container_image` shell step with structured command payload
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
- explicit ECS task execution role wiring

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
- `ecs_task_execution_role_arn`
- `ecr_url`

Current deploy shell payload behavior:

- `build_container_image` emits a structured Docker build command
- `authenticate_to_ecr` emits a structured Docker login command plus a structured AWS CLI `stdin_source`
- `push_container_image` emits a structured Docker push command
- workflow-core does not execute any of these commands

Current deploy shell payload assumptions:

- Docker build uses `working_directory="."` and build context `.`
- image references use `{ecr_url}:{image_tag}`
- ECR authentication is represented as a two-part command contract rather than a shell pipe string
- if a future executor needs different workspace layout or Dockerfile behavior, the workflow input/output contract should expand explicitly

## `scale_service` Behavior

Current plan:

- one `terraform_apply` step named `scale_service`
- generated file: `service/{service_name}/main.tf`
- reuses the existing service Terraform template and stored service state
- updates `desired_count` using `entities["replicas"]`
- prepares Terraform apply input only; Terraform execution remains outside the workflow module

Current `service_name` rule:

- use `entities["service_name"]` when provided and non-empty
- otherwise use `project_state.project_name`
- when fallback is used, the plan includes an explicit note

## `stop_service` Behavior

Current plan:

- one `terraform_apply` step named `stop_service`
- generated file: `service/{service_name}/main.tf`
- reuses the existing service Terraform template and stored service state
- forces `desired_count` to `0`
- prepares Terraform apply input only; Terraform execution remains outside the workflow module

Current `service_name` rule:

- require `entities["service_name"]` explicitly
- do not fall back to `project_state.project_name`

## `teardown_service` Behavior

Current plan:

- one `terraform_destroy` step named `teardown_service`
- generated file: `service/{service_name}/main.tf`
- reuses the existing service Terraform template
- uses deterministic defaults for omitted deploy-time fields in stored service state
- prepares Terraform destroy input only; Terraform execution remains outside the workflow module

Current `service_name` rule:

- require `entities["service_name"]` explicitly
- do not fall back to `project_state.project_name`

## Current Validation Behavior

The workflow entry point raises `ValueError` when validation fails.

Current validation rules:

- `project_state.project_name` must not be empty
- `project_state.infrastructure` must be a dictionary
- `project_state.services` must be a dictionary
- `entities` must be flat, except `environment_variables` may be a flat dictionary
- `deploy_service`, `scale_service`, `stop_service`, and `teardown_service` require non-empty `project_state.infrastructure`
- `teardown_infra` requires empty `project_state.services`
- `deploy_service` requires the seven infrastructure keys listed above
- `scale_service`, `stop_service`, and `teardown_service` currently require the same seven infrastructure keys because they reuse the service Terraform template
- `scale_service`, `stop_service`, and `teardown_service` require `project_state.services[service_name]`
- `scale_service` and `stop_service` require `project_state.services[service_name]` keys `port`, `cpu`, `memory`, and `image_tag`
- `stop_service` and `teardown_service` require explicit `entities["service_name"]`
- `scale_service` requires `entities["replicas"]` as an integer greater than or equal to `1`

Current workflow-core integration boundary:

- workflow-core plans one intent at a time
- `deploy_service` does not auto-prepend `setup_infra`
- if infrastructure is missing, validation fails and upstream should decide whether to ask for input or call `setup_infra` separately

Validation messages are joined into one `ValueError` string.

## Open B-C Discussion Items

- Decide how Person B should signal multi-step setup-then-deploy behavior.
- Decide whether Person B or Person C owns stricter normalization for CPU, memory, replicas, ports, and service names.
- Confirm that `environment_variables` should remain a flat dictionary.
- Decide whether `scale_service` should keep its current fallback-to-`project_state.project_name` behavior, or whether it should also require explicit clarification like `stop_service` and `teardown_service`.
