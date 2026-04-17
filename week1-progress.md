# InfraPilot Workflow Module — Week 1 Status Report

This report summarizes the current state of the workflow module so teammates, mentor, and reviewers can catch up quickly and use the module against the current contract. It covers the workflow module scope described in `CC Final Project Plan.pdf`.

## Week 1 Checklist

- [x] Workflow input schema is defined
- [x] Workflow output schema is defined
- [x] Basic validation is implemented
- [x] Deterministic intent dispatch is implemented
- [x] All six workflow intents are wired
- [x] Minimal Jinja2 renderer is implemented
- [x] Minimal infrastructure template is implemented
- [x] `setup_infra` now generates one real Terraform file
- [x] Local smoke verification has been run
- [ ] Service rendering is not implemented yet
- [ ] Broader infrastructure coverage is not implemented yet
- [ ] Execution logic is not implemented yet

## Current Scope

- Owns workflow planning, validation, rendering boundaries, and generated IaC file contents
- Does not own natural-language parsing, backend routing, persistence, CLI execution, or direct Terraform/Docker/AWS execution

Current real generation coverage is intentionally minimal:

- `setup_infra` generates `infra/main.tf`
- other intents still return placeholder plan steps only

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
- `entities` must be flat; nested `dict`, `list`, `tuple`, and `set` values are rejected
- `deploy_service`, `scale_service`, `stop_service`, and `teardown_service` currently require non-empty `project_state.infrastructure`

Current `setup_infra` variable resolution:

- `project_name` comes from `project_state.project_name`
- `region` uses `entities["region"]`, then `project_state.region`, then `"us-east-1"`
- `vpc_cidr` uses `entities["vpc_cidr"]`, then `"10.0.0.0/16"`

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
- `deploy_service` returns four placeholder steps
- `scale_service` returns one placeholder `terraform_apply` step
- `stop_service` returns one placeholder `terraform_apply` step
- `teardown_service` returns one placeholder `terraform_destroy` step
- `teardown_infra` returns one placeholder `terraform_destroy` step

## What `setup_infra` Generates Now

Generated file: `infra/main.tf`

Included in the template:

- Terraform block with AWS provider requirement
- `provider "aws"` using the resolved `region`
- `aws_vpc`
- `aws_ecs_cluster`
- `aws_ecr_repository`
- outputs for `vpc_id`, `ecs_cluster_name`, and `ecr_repository_url`

Not included yet:

- subnets
- internet gateway or NAT
- route tables
- ALB
- security groups
- IAM roles
- service resources

## How To Use It Now

- Use `build_execution_plan(data)` as the entry point
- Treat the return value as a deterministic planning result, not an execution result
- For `setup_infra`, read `plan.steps[0].generated_files["infra/main.tf"]` to get the rendered Terraform content
- For other intents, expect plan structure only; do not expect real generated files yet
- Keep `entities` flat until per-intent schemas are defined more strictly

Minimal `setup_infra` example:

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

## Deferred After Week 1

- service template rendering
- broader infrastructure template coverage
- Terraform execution behavior
- command generation for service workflows
- stricter per-intent entity contracts
- broader automated test coverage

## Summary

Week 1 is complete as a minimal planning-and-generation pass: the workflow module now has stable input and output schemas, basic validation, deterministic intent dispatch, and one real generated Terraform file for `setup_infra`.
