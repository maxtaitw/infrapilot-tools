# InfraPilot Workflow Core

## InfraPilot Overview

InfraPilot is a course project for turning structured backend decisions into infrastructure actions around AWS ECS on Fargate. This package is the workflow core: it receives already-structured workflow input and produces deterministic execution plans plus generated Terraform artifacts.

## Where This Module Fits

The workflow module sits between upstream interpretation and downstream execution. It receives structured intent, extracted entities, and project state, then turns them into deterministic execution plans and generated IaC artifacts.

## What This Module Owns

- deterministic workflow planning
- validation of workflow-ready inputs
- Jinja2-oriented rendering boundaries
- IaC artifact generation

## What This Module Does Not Do

- natural-language parsing
- backend API routing or persistence
- direct Terraform, Docker, or AWS execution
- CLI display or local command execution
- generic DevOps decision-making outside the scoped InfraPilot workflows

## Current Scope

This package currently supports these intents:

- `setup_infra`
- `deploy_service`
- `scale_service`
- `stop_service`
- `teardown_service`
- `teardown_infra`

Execution remains out of scope. This package generates plans and Terraform content only.

## Planned High-Level Flow

`structured intent + entities + project state -> validation -> workflow planning -> rendering -> execution plan + generated IaC files`

## Package Layout

```text
InfraPilot/
├── .gitignore
├── README.md
├── pyproject.toml
├── infrapilot_workflow/
│   └── __init__.py
├── workflow/
│   ├── __init__.py
│   ├── builders/
│   ├── validation/
│   ├── rendering/
│   │   └── renderer.py
│   ├── templates/
│   │   ├── infra/
│   │   │   └── main.tf.j2
│   │   └── service/
│   │       └── main.tf.j2
│   └── schemas/
└── tests/
    └── workflow/
```

- `workflow/` contains the internal implementation.
- `infrapilot_workflow/` is the stable public import surface intended for external consumers such as an agent repo adapter.
- `workflow/rendering/renderer.py` provides the template-loading boundary for generated files.
- `workflow/templates/infra/main.tf.j2` contains the combined infrastructure template for infrastructure setup and teardown.
- `workflow/templates/service/main.tf.j2` contains the service template reused by deploy, scale, stop, and teardown planning.

## Install And Import

For a local editable install:

```bash
cd InfraPilot
python3.13 -m venv .venv
.venv/bin/pip install -e .
```

External code should prefer the public package name:

```python
from infrapilot_workflow import (
    ProjectState,
    WorkflowInput,
    build_execution_plan,
)
```

If another repo installs this package from GitHub, the cleanest target is to publish `InfraPilot/` as the repository root. If you instead keep `InfraPilot/` as a subdirectory inside a larger repository, consumers can still install it via a Git subdirectory dependency.

Example:

```bash
pip install "git+https://github.com/<owner>/<repo>.git#subdirectory=InfraPilot"
```

## Workflow Contract Summary

Input shape:

```python
WorkflowInput(
    intent="setup_infra | deploy_service | scale_service | stop_service | teardown_service | teardown_infra",
    entities={...},
    project_state=ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure={...},
        services={...},
    ),
)
```

Output shape:

```python
ExecutionPlan(
    intent="...",
    steps=[...],
    notes=[...],
    requires_confirmation=True,
)
```

Each `PlanStep` currently includes:

- `name`
- `type`
- `description`
- `generated_files`
- optional `execution_payload`

Behavioral notes:

- This package plans one intent at a time. Upstream orchestrators may call `setup_infra` and `deploy_service` separately, but workflow-core does not combine them into one plan.
- `deploy_service` still requires existing infrastructure state. Missing required infrastructure remains a validation failure.
- `deploy_service` and `scale_service` may fall back to `project_state.project_name` for `service_name`.
- `stop_service` and `teardown_service` require explicit `entities["service_name"]`.
- `teardown_infra` requires empty `project_state.services`.
- `teardown_service` tolerates sparse stored service metadata by filling omitted deploy-time fields with deterministic defaults during destroy planning.
- Service-rendering intents expect `project_state.infrastructure` to include `ecs_task_execution_role_arn`, and the rendered ECS task definition wires that value into `execution_role_arn`.
- `deploy_service` shell steps now emit structured `execution_payload` data for downstream executors. The current payload shape is:
  - `command.binary`
  - `command.args`
  - optional `command.env`
  - optional `command.working_directory`
  - optional `stdin_source` with the same nested command shape
- Current deploy payload assumptions are intentionally narrow:
  - Docker build uses `working_directory="."` and build context `.`
  - image references use `{ecr_url}:{image_tag}`
  - ECR authentication is modeled as `docker login --password-stdin` plus an AWS CLI `stdin_source`
  - if downstream runtime layout differs, the workflow contract should expand instead of expecting executors to guess
- This package does not execute Terraform, Docker, or AWS commands.

## Local Verification

Use Python 3.10+ for local verification. Python 3.13 is the version used for the latest local checks.

```bash
cd InfraPilot
python3.13 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

## Usage Guidance

- Keep this package deterministic. Do not move natural-language interpretation into this repo.
- Treat this package as workflow core, not as an execution service.
- Do not add direct Terraform, Docker, or AWS execution here.
- External agent repos should wrap this package with adapter tools instead of rewriting the planner logic.

## Next Steps

Future iterations should harden Terraform coverage, refine downstream execution handling around the new shell payload contract, and preserve the current boundary where backends or orchestrators coordinate multi-step flows outside this deterministic core.
