# Worklog

## Week 1 Minimal Renderer + `setup_infra` File Generation

- Goal: Add the smallest real rendering path so `setup_infra` returns one generated Terraform file without changing the engine contract or adding execution logic.
- Completed: Added a local Jinja2 renderer, added `workflow/templates/infra/main.tf.j2`, wired `workflow/engine.py` so `setup_infra` generates `infra/main.tf`, synced README and AGENTS status text, and ran local smoke verification in `.venv`.
- Deferred Intentionally: Service rendering, broader infrastructure resources, Terraform execution behavior, tracked dependency files, and any packaging or environment-policy changes.
- Notes: Kept `setup_infra` explicitly minimal in descriptions and notes, did not add a Terraform `locals` block, and used `.venv` only for local verification.
- Next Step: Add the next minimal template or workflow behavior only after its scope and contract are explicitly approved.

## Week 2 Minimal Service Rendering + Contract Handoff

- Goal: Add the smallest real `deploy_service` rendering path and make the current workflow contract clear enough for teammate integration.
- Completed: Added a minimal ECS service template, wired `deploy_service` to generate `service/{service_name}/main.tf`, added narrow deploy infrastructure validation, added tracked `unittest` workflow contract tests, created `backend-workflow-handoff.md`, refreshed `B-C-contract.md`, and updated `week2-progress.md`.
- Deferred Intentionally: Real shell commands, Terraform execution, backend/CLI integration code, broader infrastructure coverage, setup-then-deploy multi-step behavior, scale/stop/teardown rendering, and real AWS validation.
- Notes: Kept shell steps as placeholders, made `service_name` fallback explicit in plan notes, kept `environment_variables` as a flat dictionary, and kept the handoff docs based only on implemented behavior.
- Next Step: Decide whether to prepare Terraform validation for the current minimal templates or wait until broader infrastructure coverage is added.

## Week 2 Infrastructure Template Expansion

- Goal: Move `setup_infra` closer to the original Person C infrastructure-template scope while still generating one Terraform file.
- Completed: Expanded `workflow/templates/infra/main.tf.j2` to include VPC networking, public/private subnets, internet gateway, NAT gateway, route tables, ALB, security groups, ECS cluster capacity providers, ECR repository, ECS task execution role, and fuller outputs.
- Deferred Intentionally: Terraform execution, real AWS validation, template hardening from cloud feedback, backend/CLI execution integration, and remaining workflow rendering.
- Notes: Kept the existing `WorkflowInput` and `ExecutionPlan` schemas unchanged and continued using only `project_name`, `region`, and `vpc_cidr` for `setup_infra`. Terraform CLI is now installed locally and rendered infra/service templates pass `fmt`, `init`, and `validate`.
- Next Step: Coordinate backend integration or plan real AWS validation with approved credentials and execution boundaries.

## Week 2 Backend Integration Discovery

- Goal: Check whether the workflow module can be wired into Person A's backend in this checkout.
- Completed: Inspected the repository for backend app, API route, and workflow integration files.
- Deferred Intentionally: Backend scaffold creation, route implementation, persistence, and execution behavior.
- Notes: No backend source files are present in this checkout, so there is no safe integration point to edit yet.
- Next Step: Bring Person A's backend source into the shared checkout, then wire the existing `build_execution_plan(...)` entry point into the agreed route.

## Week 2 `teardown_infra` Generation

- Goal: Give infrastructure teardown the same generated Terraform input as setup while keeping execution outside the workflow module.
- Completed: Wired `teardown_infra` to return one `terraform_destroy` step with `infra/main.tf`, reused the existing setup-infra variable resolver and infra template, updated contract tests, and refreshed Week 2 status.
- Deferred Intentionally: Terraform destroy execution, state management, AWS credential handling, backend routing, and service teardown rendering.
- Notes: This prepares destroy-plan file content only; it does not run Terraform or decide how state is stored.
- Next Step: Wait for backend source files or choose the next service lifecycle intent after deciding whether it should be Terraform-driven or command/API-driven.
