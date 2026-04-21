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
- Deferred Intentionally: Terraform execution, real Terraform validation, real AWS validation, template hardening from cloud feedback, backend/CLI execution integration, and remaining workflow rendering.
- Notes: Kept the existing `WorkflowInput` and `ExecutionPlan` schemas unchanged and continued using only `project_name`, `region`, and `vpc_cidr` for `setup_infra`.
- Next Step: Run Terraform `fmt` and `validate` once Terraform is available, then fix any syntax or provider-level issues before real AWS testing.
