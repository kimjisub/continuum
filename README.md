# Continuum

Continuum is an agent-neutral context router and evidence ledger.

It sits between **sources** and **workflows**:

```text
Sources → Continuum Core → Workflows
```

- Sources: Slack, Plaud, Mail, Calendar, Reminders, browser/session/file/manual input
- Core: streams, items, artifacts, segments, workflow state, runs, outputs, lineage, trust
- Workflows: daily report, morning report, diary, todo/calendar planner, GBrain fanout, future agents

## Product values

1. **Capture observable context with provenance**
   - Capture observable context from accessible sources with source, actor, run, trust, and sensitivity metadata.
2. **Route relevant context without silent drops**
   - Route relevant segments to workflows and make processed/skipped/failed/unrouted states explicit.
3. **Keep context user-owned and agent-neutral**
   - Context belongs to the user, not to a specific agent runtime.

## Repository layout

```text
.
├── docs/                  # Planning, architecture, source/workflow guides
├── src/continuum/          # Continuum code package
├── tests/                 # Tests for code package
├── runtime/               # Local runtime workspace placeholder; real data is gitignored
├── pyproject.toml         # Python project metadata
└── README.md
```

## Code area vs runtime area

Continuum keeps code and runtime data separate.

### Code area

Committed to git:

```text
docs/
src/
tests/
pyproject.toml
README.md
```

This contains the product design, implementation, tests, adapters, CLI, schemas, and guides.

### Runtime area

Not committed to git:

```text
runtime/continuum.db
runtime/artifacts/
runtime/outputs/
runtime/logs/
runtime/tmp/
```

Runtime contains local state, collected data, generated reports, drafts, logs, and temporary files. The repo includes only `runtime/README.md` and `runtime/.gitignore` to document the expected shape.

## Current status

Planning/bootstrap phase. See:

```text
docs/continuum-architecture-plan.md
```
