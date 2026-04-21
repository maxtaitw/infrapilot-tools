# InfraPilot Workflow Module

## InfraPilot Overview

InfraPilot is a course project for turning structured backend decisions into infrastructure actions around AWS ECS on Fargate. This repository area currently focuses only on the workflow module described in `CC Final Project Plan.pdf`.

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

## Current Iteration Scope

This iteration includes concrete schemas, a validation skeleton, a minimal Jinja2 renderer, expanded `setup_infra` file generation, and minimal `deploy_service` service file generation. Execution behavior and remaining workflow coverage stay deferred.

## Planned High-Level Flow

`structured intent + entities + project state -> validation -> workflow planning -> rendering -> execution plan + generated IaC files`

## Initial Folder Layout

```text
InfraPilot/
├── AGENTS.md
├── README.md
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

- `workflow/` is named by responsibility rather than ownership.
- `workflow/rendering/renderer.py` provides the minimal template-loading boundary for generated files.
- `workflow/templates/infra/main.tf.j2` is one combined infrastructure file for `setup_infra`.
- `workflow/templates/service/main.tf.j2` is intentionally limited to one minimal service file for `deploy_service`.
- `schemas/` is reserved for future workflow-facing data contracts once team boundaries are finalized.

## Local Verification Setup

Use Python 3.10+ for local verification. Python 3.13 is the version used for the latest local checks.

```bash
cd InfraPilot
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

## How Teammates Should Use This Repo

- Read `AGENTS.md` first for scope and working rules.
- Treat `CC Final Project Plan.pdf` as the main product boundary.
- Keep changes incremental and easy to review.
- Do not add execution logic here; this module should produce plans and files, not run commands.

## Next Steps

Future iterations should validate and harden the infrastructure template, expand service rendering beyond `deploy_service`, and keep execution behavior outside this module unless that boundary is approved.
