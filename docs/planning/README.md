# Continuum Planning Docs

The original long architecture plan is split into ordered planning documents.

| Order | Document | Contents |
|---:|---|---|
| 00 | [Overview, Values, Philosophy, Principles](00-overview-values-philosophy-principles.md) | Why Continuum exists, values, philosophy, implementation principles |
| 01 | [System Architecture and Storage](01-system-architecture-and-storage.md) | High-level architecture and runtime storage layout |
| 02 | [Data Model — Core Entities](02-data-model-core.md) | Terms, streams, cursors, items, artifacts, segments |
| 03 | [Data Model — Workflows, Runs, and Outputs](03-workflows-runs-and-outputs.md) | Workflows, queues, runs, workflow packages, context bundles, lineage, outputs, drafts |
| 04 | [Data Model — Actors and Trust](04-actors-and-trust.md) | Source actors, actor links, trust assessments, evidence conflicts |
| 05 | [Source Sync and Ingest](05-source-sync-and-ingest.md) | Slack/append-stream handling, polling, push, trigger policy |
| 06 | [Runtime, CLI, and MCP](06-runtime-cli-mcp.md) | Install/onboarding model, daemon model, CLI and MCP surfaces |
| 07 | [Use Cases and Guarantees](07-use-cases-and-guarantees.md) | Daily/morning report, diary, todo/calendar, GBrain, guarantees/non-guarantees |
| 08 | [Implementation, Scope, and Success Criteria](08-implementation-scope-and-success.md) | Phases, non-goals, success criteria, final summary |
| 09 | [ERD](09-erd.md) | Mermaid entity relationship diagram |
| 10 | [Entity Reference and Mutability](10-entity-reference-and-mutability.md) | Entity explanations, naming, mutability rules |

## Source-of-truth rule

Use these files as the source of truth for future planning edits.
