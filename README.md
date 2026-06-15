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

## Target user experience

End users should not need to clone this repository.

```bash
uv tool install continuum
continuum setup
continuum doctor

# Agent integration, depending on host:
hermes skills install continuum
# or
hermes mcp add continuum --command "continuum mcp serve"
```

Repository clone is for contributors only:

```bash
git clone https://github.com/kimjisub/continuum
cd continuum
uv sync
uv run continuum
```

## Runtime / daemon model

Continuum is primarily a **CLI + local runtime DB**. It should not require an always-on daemon for basic use.

- **Default v1:** no daemon. Cron/Hermes/shell invokes `continuum collect`, `continuum route`, `continuum workflows ...` as short-lived commands.
- **Optional daemon later:** `continuum daemon` may run local scheduling/watchers, queue workers, and health checks.
- **MCP server:** `continuum mcp serve` is a long-running process, but only needed when an agent host wants MCP tools.

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

Planning/bootstrap phase. Start with:

```text
docs/planning/README.md
```

The legacy aggregate plan at `docs/continuum-architecture-plan.md` now points to the split planning docs.
