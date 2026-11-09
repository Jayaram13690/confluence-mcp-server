# SDD master prompt (copy-paste to start any session)

You are working in the Confluence MCP Server repo under Spec-Driven Development.

1. Read `CLAUDE.md`, then `docs/sdd/spec.md`, `openapi.yaml`, `plan.md`, `tasks.md`, `REPORT.md`.
2. My request: <describe change or task id, e.g. T-7.1>.
3. Work in gated phases and STOP after each for my approval:
   - Specify: propose the exact spec.md / openapi.yaml diff (new/changed FR/NFR/AC ids).
   - Plan: update plan.md (design, files touched, risks).
   - Tasks: add ordered, checkable tasks citing requirement ids.
   - Implement: tests first, one task per commit, respect layering and security rules in CLAUDE.md.
   - Verify: run ruff + pytest --cov, update REPORT.md, list any requirement not met.
4. Never change code behavior without a matching spec change. Report spec/code drift instead of silently fixing it.
