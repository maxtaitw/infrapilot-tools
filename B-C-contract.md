

# B-C Contract Draft

## Goal

This document defines the current working boundary between:

- the upstream intent/entity layer
- the workflow module

The goal is to make integration easier and reduce guessing.

---

## Responsibility Split

### Upstream layer owns
- understanding natural-language user requests
- deciding the intent
- extracting entities
- sending structured input

### Workflow module owns
- validating structured input
- combining input with project state
- deciding the workflow shape
- returning a deterministic execution plan

---

## Supported Intents

Current scoped intents:

- `setup_infra`
- `deploy_service`
- `scale_service`
- `stop_service`
- `teardown_service`
- `teardown_infra`

---

## Input Shape

The workflow module expects this structure:

```json
{
  "intent": "...",
  "entities": {},
  "project_state": {}
}
```

### Current expectations

#### `intent`
Must be one of the 6 supported intents above.

#### `entities`
- flat dictionary for now
- no nested objects unless we explicitly agree later

#### `project_state`
Current minimum shape:

```json
{
  "project_name": "string",
  "region": "string or null",
  "infrastructure": {},
  "services": {}
}
```

---

## Suggested Entities by Intent

These are the current suggested fields.
They are not fully frozen yet, but should be the default direction.

### `setup_infra`
Possible fields:
- `region`
- `cluster_name`
- `vpc_cidr`

### `deploy_service`
Possible fields:
- `service_name`
- `port`
- `cpu`
- `memory`
- `replicas`
- `environment_variables`
- `image_tag`

### `scale_service`
Possible fields:
- `service_name`
- `replicas`

### `stop_service`
Possible fields:
- `service_name`

### `teardown_service`
Possible fields:
- `service_name`

### `teardown_infra`
- no required fields for now

---

## Workflow Module Output

Current output shape:

```json
{
  "intent": "...",
  "steps": [],
  "notes": [],
  "requires_confirmation": true
}
```

Each step currently looks like:

```json
{
  "name": "...",
  "type": "...",
  "description": "...",
  "generated_files": {}
}
```

Current step types:
- `terraform_apply`
- `terraform_destroy`
- `shell_command`

Important note:
- `generated_files` is currently only a placeholder
- real file generation is not implemented yet

---

## Current Workflow Shapes

### `setup_infra`
- 1 placeholder `terraform_apply` step

### `deploy_service`
- build container image
- authenticate to ECR
- push image
- apply service infrastructure

### `scale_service`
- 1 placeholder `terraform_apply` step

### `stop_service`
- 1 placeholder `terraform_apply` step

### `teardown_service`
- 1 placeholder `terraform_destroy` step

### `teardown_infra`
- 1 placeholder `terraform_destroy` step

These are current placeholder workflow shapes only.

---

## What Is Already Stable Enough

The following are stable enough to align on now:

- the 6 intent names
- top-level input shape
- top-level output shape
- deterministic workflow dispatch exists
- `requires_confirmation = true`

---

## Open Questions To Discuss

### 1. Missing values
If a user leaves out values, who should fill them?

Examples:
- `scale to 5` with no service name
- `deploy my app` with no cpu/memory/replicas
- `stop it` with no service name

Need to decide whether:
- upstream fills values from context/state
- workflow module fills values from project state when safe
- missing values should remain missing and be treated as validation/clarification issues

### 2. Multi-step behavior
Example:
- user asks for `deploy_service`
- infrastructure does not exist

Need to decide whether:
- upstream should explicitly signal multi-step behavior
- workflow module should infer it from `intent + project_state`
- missing infrastructure should simply be treated as an error

### 3. `environment_variables` shape
Still needs agreement.

Possible directions:
- flat dictionary
- list of key/value pairs

### 4. Future generated files contract
Likely future direction:

```json
{
  "generated_files": {
    "infra/main.tf": "...",
    "service/main.tf": "..."
  }
}
```

Still needs confirmation later.

---

## Immediate Next Step

Suggested next discussion with B:

1. confirm the 6 intent names
2. confirm the suggested entity fields
3. decide:
   - missing value policy
   - multi-step policy
   - `environment_variables` shape

Once those are aligned, integration between the intent/entity layer and the workflow module should be much smoother.