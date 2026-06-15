# Continuum runtime area

This directory documents the local runtime workspace shape.

Runtime data is intentionally **not committed to git**.

Expected local structure:

```text
runtime/
├── continuum.db      # SQLite state/index DB
├── artifacts/        # Raw and derived source files
├── outputs/          # Reports, proposals, drafts, generated files
├── logs/             # Worker/CLI logs
└── tmp/              # Temporary files
```

Principle:

```text
code area = committed
runtime area = local, inspectable, recoverable, gitignored
```
