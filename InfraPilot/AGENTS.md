# InfraPilot Workflow Module Notes

## Source of Truth

- `../CC Final Project Plan.pdf` is the primary design reference for scope, responsibilities, and supported workflow shapes.
- If later notes conflict with the final project plan, prefer the final project plan unless the team explicitly agrees to a change and documents that decision.
- This module should evolve by small, reviewable steps. Do not expand scope implicitly.

## Module Purpose

This repository area owns the workflow-planning layer of InfraPilot. Which is the "Part 3 — Person C: Workflows and Code Generation" section in `../CC Final Project Plan.pdf` .
Its responsibilities are:

- deterministic workflow planning
- validation
- template rendering
- IaC artifact generation

This module translates structured backend inputs into deterministic plans and generated artifacts.

## Out of Scope

This module does not own:

- natural-language parsing
- direct Terraform execution
- direct Docker execution
- direct AWS command execution
- CLI execution logic
- backend API routing
- persistence ownership
- generic DevOps assistant behavior

## Naming Rules

- Do not use contributor-based naming in code, docs, modules, classes, comments, or interfaces.
- Avoid names such as `person_c`, `for_person_c`, or similar ownership-based labels.
- Name packages, files, classes, and functions by responsibility, not by teammate.
- Prefer names such as `workflow`, `validation`, `rendering`, `schemas`, `engine`, and `builders`.
- Write documentation so that someone outside the original team can understand the module without needing project-role context.

## Import Rules

- Prefer relative imports for internal package-to-package imports within the `workflow` module.
- Keep imports consistent across the module.
- Avoid fragile import patterns that depend on a specific working directory.
- Do not introduce path hacks or runtime `sys.path` manipulation.

## Design Principles

- Keep modules small, explicit, and readable.
- Prefer deterministic logic over autonomous behavior.
- Keep abstractions minimal and easy to trace.
- Optimize for teammate usability over cleverness.
- Favor composition over deep inheritance.
- Keep public interfaces small and stable.
- Separate planning, validation, rendering, and generated artifacts into distinct responsibilities.
- Keep behavior easy to test without external services.

## Documentation Requirements

- Every top-level module should have a clear purpose.
- README content should explain what this module does, what it does not do, what inputs it expects, and what outputs it returns.
- Docstrings should explain intent and constraints, not restate obvious code.
- Comments should capture why a decision exists, especially when tied to project scope or future integration.
- When behavior is intentionally deferred, document that clearly rather than implying it already exists.

## Interface and Contract Rules

- Input boundary: structured intent, extracted entities, and project state.
- Output boundary: ordered execution plan and generated file contents.
- Keep schema definitions explicit and versionable.
- Do not leak CLI-specific or backend-routing-specific concerns into workflow models unless explicitly approved.
- Do not add fields to shared contracts casually; prefer additive, documented changes.
- When in doubt, keep types conservative and easy to understand.

## Validation Rules

- Keep validation logic separate from workflow dispatch logic.
- Start with lightweight structural validation before domain-heavy rules.
- Do not mix cloud execution checks into planning-time validation.
- Add stricter validation only when the team agrees the corresponding contract is stable.

## Testing Expectations

- Add tests alongside behavior as the module grows.
- Prefer small, deterministic unit tests over integration-heavy tests in early iterations.
- Keep test names descriptive and tied to behavior.
- Avoid introducing external cloud dependencies into unit tests.

## Repo Conventions

- Plan before execute.
- Keep each change small and reviewable.
- Avoid unrelated refactors.
- Prefer clear naming over clever abstractions.
- Preserve simple boundaries between planning, validation, rendering, and generated artifacts.
- Do not add dependencies without approval.
- Do not add frameworks or abstractions before there is a clear need.
- If scope grows, update this file before updating implementation.

## Collaboration Notes

- Upstream systems provide structured intent and entity data.
- Backend integration is responsible for API routing and project-state flow.
- Downstream consumers use plan payloads for display and local execution.
- This module should remain understandable and usable even if ownership changes in the future.

## Current Milestone

- Documentation, schemas, validation skeleton, and workflow engine skeleton remain the baseline
- A minimal renderer now exists
- A minimal infrastructure template now exists
- `setup_infra` now returns one generated Terraform file with minimal coverage
- Service rendering and broader infrastructure coverage remain deferred
- No execution logic yet
    
