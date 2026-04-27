# Part 3 Workflow-Core Implementation Plan

## Overview

This plan narrows Part 3 to work that belongs inside the workflow core only.

Current workflow-core responsibilities:

- structured input validation
- deterministic workflow planning
- Terraform file rendering
- execution-plan construction

Out of scope for this plan:

- natural-language parsing
- LangChain or agent adapter logic
- backend routing or persistence
- Terraform, Docker, or AWS execution
- runtime orchestration that depends on post-apply infrastructure outputs
- broad architecture redesign

The goal is to finish the deterministic workflow core cleanly, then leave stable seams for downstream agents, adapters, and executors.

## Workflow-Core Principles

1. Keep deterministic planning and safety rules in the workflow core.
2. Do not push user-clarification logic into the workflow core.
3. When workflow-core emits shell execution payloads, keep them structured, deterministic, and explicit about their assumptions.
4. Do not compose multi-step runtime workflows that depend on infrastructure outputs not yet present in `project_state`.
5. Prefer small, reviewable commits that keep tests and public contract docs in sync.

## Proposed Commits In Order

### 1. `feat: wire ecs task execution role into service planning`

Purpose:

- The infrastructure template already outputs `ecs_task_execution_role_arn`, but the service workflow and service Terraform template do not consume it yet.
- This is a correctness gap in the current deploy/scale/stop/teardown service plans because ECS task definitions should reference the execution role explicitly.

Scope:

- Add `ecs_task_execution_role_arn` to the required infrastructure contract for service-rendering intents.
- Pass the value through service variable resolution in `engine.py`.
- Render it into `workflow/templates/service/main.tf.j2`.
- Update contract tests and public docs.

Likely files to change:

- `InfraPilot/workflow/engine.py`
- `InfraPilot/workflow/validation/basic.py`
- `InfraPilot/workflow/templates/service/main.tf.j2`
- `InfraPilot/tests/workflow/test_engine.py`
- `B-C-contract.md`
- `backend-workflow-handoff.md`
- `review-summary.md`

Testing / verification:

- `py_compile` for touched Python files
- `unittest` coverage for all service intents checking the rendered task definition includes `execution_role_arn`
- local Terraform `fmt` and `validate` on rendered service plans

Risks or notes:

- This is a cross-cutting service contract change, so it should land before other service-template refinements.
- Keep it limited to value wiring and validation, not IAM policy redesign.

### 2. `fix: guard teardown_infra when service state still exists`

Purpose:

- `teardown_infra` currently renders destroy input even if `project_state.services` still contains service state.
- The planner should reject infrastructure teardown while service state is still present, unless the team later adds an explicit override outside the workflow core.

Scope:

- Add a deterministic safety guard for `teardown_infra`.
- Reject teardown when `project_state.services` is non-empty.
- Keep the guard inside the validation/planning boundary only.

Likely files to change:

- `InfraPilot/workflow/validation/basic.py`
- `InfraPilot/tests/workflow/test_engine.py`
- `B-C-contract.md`
- `backend-workflow-handoff.md`
- `review-summary.md`

Testing / verification:

- add a negative test where `teardown_infra` receives non-empty `project_state.services`
- keep existing `teardown_infra` generation tests passing

Risks or notes:

- Do not invent a policy-heavy approval or override mechanism here.
- Confirmation and override behavior belong to downstream orchestration layers.

### 3. `feat: add structured execution payloads to deploy shell steps`

Purpose:

- Current deploy shell steps already represent real workflow stages: build image, authenticate to ECR, and push image.
- Downstream executors should not have to reconstruct those commands from human-readable descriptions.
- Workflow-core should emit machine-readable command specs while still leaving actual process execution, retries, credentials, and logging to downstream layers.

Scope:

- Add one optional `execution_payload` field to `PlanStep`.
- Populate it for the three `deploy_service` shell steps only.
- Keep the payload structured:
  - `command.binary`
  - `command.args`
  - optional `command.env`
  - optional `command.working_directory`
  - optional `stdin_source` with the same nested command shape
- Keep Terraform-only steps at `execution_payload=None`.
- Do not add subprocess wrappers, runner policy, agent abstractions, or direct execution.

Likely files to change:

- `InfraPilot/workflow/schemas/plans.py`
- `InfraPilot/tests/workflow/test_engine.py`
- `B-C-contract.md`
- `backend-workflow-handoff.md`
- `InfraPilot/README.md`

Testing / verification:

- `py_compile`
- `unittest` assertions that shell steps serialize with structured payloads
- regression checks that Terraform-only steps still serialize cleanly with `execution_payload=None`

Risks or notes:

- Current payload assumptions must be documented explicitly:
  - Docker build context is `.` relative to the executor working directory
  - ECR authentication is modeled as a `docker login --password-stdin` command plus a structured AWS CLI `stdin_source`
  - image references use `{ecr_url}:{image_tag}`
- If future runtime layouts need different build contexts, Dockerfiles, or auth flows, the workflow contract should expand rather than relying on executor guesswork.

### 4. `test: expand workflow contract coverage for lifecycle safety and service rendering`

Purpose:

- The repo now has intent-specific rules spread across engine, validation, and templates.
- A dedicated test-hardening commit makes those rules explicit and protects them from regression as Part 3 closes out.

Scope:

- Expand coverage across:
  - positive cases
  - missing-field validation cases
  - service-name fallback vs. explicit-name behavior
  - service-role wiring
  - teardown-infra safety guard
  - sparse-state teardown behavior
  - optional execution metadata serialization
- Keep tests in the current `unittest` style unless a concrete helper is clearly justified.

Likely files to change:

- `InfraPilot/tests/workflow/test_engine.py`
- optionally add one or two small fixture helpers if the test file becomes too dense

Testing / verification:

- `py_compile`
- full `unittest discover`
- local Terraform `fmt` and `validate` smoke checks for any newly rendered plan variants

Risks or notes:

- Keep this focused on coverage and regression protection, not feature changes.
- If test data becomes repetitive, extract only small helper builders rather than creating a large new test framework.

### 5. `docs: sync README and public workflow contract docs`

Purpose:

- After the behavior changes above land, the README and public contract docs need one final cleanup pass so external readers do not have to infer current behavior from code.
- This is the last documentation sweep, not the place to change planner behavior.

Scope:

- Update:
  - `InfraPilot/README.md`
  - `B-C-contract.md`
  - `backend-workflow-handoff.md`
  - `review-summary.md`
  - any JSON shape examples if they have become stale
- Make current intent behavior, validation expectations, and service-role wiring explicit.
- Document the currently intentional boundaries:
  - no natural-language parsing
  - no runtime orchestration
  - no direct execution

Likely files to change:

- docs only

Testing / verification:

- manual doc consistency review against engine and tests
- JSON syntax validation if example files change

Risks or notes:

- Keep this commit documentation-only.
- Do not hide behavior changes inside the docs cleanup commit.

## Explicitly Deferred From Workflow-Core

The following items are intentionally not part of this workflow-core plan.

### Deferred 1. Shell command execution and runtime policy

Reason:

- Workflow-core now emits structured command specs for deploy shell steps.
- It still must not:
  - spawn subprocesses
  - own retry policy
  - own stdout/stderr capture
  - own credential sourcing
  - own workspace/runtime bootstrapping

Owner:

- downstream executor contract
- adapter or backend integration layer

### Deferred 2. Reverting stop/teardown semantics back to looser fallback behavior

Reason:

- The current safer behavior is intentional:
  - `stop_service` requires explicit `service_name`
  - `teardown_service` requires explicit `service_name`
  - `teardown_service` tolerates sparse stored state by using deterministic defaults
- Reintroducing fallback-driven targeting would weaken safety for operational and destructive intents.

Owner:

- none for now unless the team explicitly changes the public contract

### Deferred 3. Multi-step setup-plus-deploy composition inside the workflow core

Reason:

- `deploy_service` currently depends on infrastructure values already present in `project_state.infrastructure`.
- `setup_infra` currently generates Terraform input, but it does not execute and does not resolve post-apply runtime outputs back into `project_state`.
- Because of that, composing setup-plus-deploy in one deterministic planning pass is not reliable under the current contract.

Preferred handling:

- let upstream orchestration or backend/executor run:
  1. `setup_infra`
  2. execution/apply
  3. project state update
  4. `deploy_service`

Owner:

- backend or agent/executor orchestration layer

## Dependencies And Order Constraints

1. Commit 1 should land before further service-template refinements because it changes the service intent infrastructure contract.
2. Commit 2 is independent of execution-metadata work and can land early as a safety improvement.
3. Commit 3 should stay schema-only; it does not imply concrete command generation.
4. Commit 4 should follow the feature commits so the final test matrix reflects the settled workflow-core contract.
5. Commit 5 should be last so public docs match the implemented state.

Recommended sequence:

1. service role wiring
2. teardown-infra safety guard
3. optional execution metadata field
4. test hardening
5. docs sync
