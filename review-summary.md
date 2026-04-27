# Review Summary

This summary is for teammate and mentor review of the current Person C workflow/code-generation state.

## What To Review

- `InfraPilot/workflow/engine.py`: current workflow dispatch, expanded `setup_infra` generation, and minimal `deploy_service` generation.
- `InfraPilot/workflow/validation/basic.py`: current structural validation, required service infrastructure keys including ECS task execution role wiring, and stored service-state checks for non-deploy service intents.
- `InfraPilot/workflow/templates/infra/main.tf.j2`: combined infrastructure Terraform template.
- `InfraPilot/workflow/templates/service/main.tf.j2`: minimal ECS service Terraform template.
- `InfraPilot/tests/workflow/test_engine.py`: tracked workflow contract tests.
- `B-C-contract.md`: current B/C intent/entity contract.
- `backend-workflow-handoff.md`: backend integration handoff for Person A.
- `integration-examples/`: JSON input/output-shape examples for backend wiring.
- `week2-progress.md`: current Week 2 status report.

## How To Verify

From `InfraPilot/`:

```bash
PYTHONPYCACHEPREFIX=/tmp/pycache .venv/bin/python -m py_compile workflow/engine.py workflow/validation/basic.py workflow/rendering/renderer.py tests/workflow/test_engine.py
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
terraform -chdir=/tmp/infrapilot-template-validation/infra fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/infra init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/infra validate
terraform -chdir=/tmp/infrapilot-template-validation/service/api fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/service/api init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/service/api validate
terraform -chdir=/tmp/infrapilot-template-validation/scale-service/api fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/scale-service/api init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/scale-service/api validate
terraform -chdir=/tmp/infrapilot-template-validation/stop-service/api fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/stop-service/api init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/stop-service/api validate
terraform -chdir=/tmp/infrapilot-template-validation/teardown-service/api fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/teardown-service/api init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/teardown-service/api validate
terraform -chdir=/tmp/infrapilot-template-validation/teardown-infra fmt -check -diff
terraform -chdir=/tmp/infrapilot-template-validation/teardown-infra init -backend=false
terraform -chdir=/tmp/infrapilot-template-validation/teardown-infra validate
```

Latest local result:

```text
Ran 15 tests in 0.007s
OK
```

JSON examples were validated with:

```bash
python3 -m json.tool
```

## Current Status

- `setup_infra` generates one combined Terraform file: `infra/main.tf`.
- `deploy_service` generates one minimal Terraform file on its Terraform step: `service/{service_name}/main.tf`.
- `scale_service` generates one service Terraform file on its apply step: `service/{service_name}/main.tf`.
- `stop_service` generates one service Terraform file on its apply step: `service/{service_name}/main.tf`.
- `teardown_service` generates one service Terraform file on its destroy step: `service/{service_name}/main.tf`.
- `teardown_infra` generates one combined Terraform file on its destroy step: `infra/main.tf`.
- `teardown_infra` now rejects planning when `project_state.services` is non-empty.
- Service-rendering intents now require `ecs_task_execution_role_arn` in `project_state.infrastructure`, and rendered ECS task definitions include `execution_role_arn`.
- `PlanStep` now exposes an optional structured `execution_payload` field.
- The first three `deploy_service` shell steps still have empty `generated_files`, but now include machine-readable shell command payloads.
- Those shell payloads currently assume Docker build context `.` and model ECR login as a Docker command plus an AWS CLI `stdin_source`; executors still own runtime execution behavior.
- workflow-core still plans one intent at a time; setup and deploy remain separate upstream calls.
- `deploy_service` and `scale_service` still fall back to `project_state.project_name` when `service_name` is missing or blank, and the plan records that fallback in `notes`.
- `stop_service` and `teardown_service` now require explicit `service_name` instead of falling back to `project_state.project_name`.
- `teardown_service` now tolerates sparse stored service metadata by filling omitted deploy-time fields with deterministic defaults for destroy planning.
- Terraform `v1.14.9` is installed locally.
- Rendered infra, service, scale-service, stop-service, teardown-service, and teardown-infra Terraform files pass `fmt`, `init`, and `validate` in `/tmp/infrapilot-template-validation`.

## Deferred

- shell command execution
- Terraform execution
- backend and CLI integration code
- infrastructure hardening after real AWS validation
- multi-intent orchestration inside workflow-core
- real AWS validation
