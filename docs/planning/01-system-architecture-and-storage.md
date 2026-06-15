# System Architecture and Storage

> Part of the Continuum planning docs. See [planning index](README.md).

## 4. 전체 아키텍처

```text
External Systems
  ↓
Connectors
  - polling connector
  - push webhook connector
  - agent/MCP connector
  ↓
Continuum Ledger SQLite
  - streams
  - items
  - artifacts
  - segments
  - cursors
  - workflow states
  - lineage
  ↓
Workflows
  - morning report
  - daily report
  - diary
  - todo/calendar planner
  - gbrain fanout
  - future agents
  ↓
Outputs
  - reports
  - todos
  - calendar events
  - GBrain updates
  - notifications
```

파일은 raw/large artifact 저장소로 쓰고, SQLite는 상태와 인덱스의 SSOT가 된다.

---

## 5. 저장 경로

현재는 기존 `ContextArchive`를 유지하되, 내부 의미를 Continuum 기준으로 재정의한다.

```text
~/ContextArchive/
  _state/
    continuum.db
  _inbox/
    webhook-events/
    manual-drop/
  YYYY-MM-DD/
    plaud/
    slack/
    mail/
    calendar/
    reminders/
    normalized/
    derived/
```

향후 rename 가능:

```text
~/Continuum/
  _state/continuum.db
  YYYY-MM-DD/...
```

초기에는 migration 비용을 줄이기 위해 `~/ContextArchive`를 그대로 사용한다.

---
