# Data Model — Workflows, Runs, and Outputs

> Part of the Continuum planning docs. See [planning index](README.md).

### 6.6 Workflows

workflow는 사용처다. source와 독립적이다.

예:

- `morning_report`
- `daily_report`
- `diary`
- `todo_planner`
- `calendar_planner`
- `gbrain_fanout`
- `weekly_review`

```sql
CREATE TABLE workflows (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  display_name TEXT,
  mode TEXT NOT NULL, -- deterministic | agent
  trigger_policy_json TEXT, -- v2: push/schedule trigger policy
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

---

### 6.7 Workflow packages

Workflow package는 host-agnostic workflow 정의다.

`workflows` table이 runtime 등록 상태라면, workflow package는 Hermes/Claude Code/Codex/MCP/local cron이 공유할 수 있는 portable spec이다.

```sql
CREATE TABLE workflow_packages (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  version TEXT NOT NULL,
  package_path TEXT NOT NULL,
  input_contract_json TEXT NOT NULL,
  output_contract_json TEXT NOT NULL,
  required_capabilities_json TEXT,
  safety_policy_json TEXT,
  guide_path TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

규칙:

- package는 특정 agent prompt가 아니라 host-agnostic spec이어야 한다.
- host별 adapter는 package를 읽어 자기 실행 방식으로 변환할 수 있다.
- package에는 “무슨 context bundle을 입력으로 받고, 어떤 output을 만들며, 어떤 side effect 권한이 필요한지”가 명시되어야 한다.

---

### 6.8 Workflow state

각 workflow가 각 segment를 어떻게 처리했는지 기록한다.

```sql
CREATE TABLE workflow_segment_state (
  workflow_id INTEGER NOT NULL,
  segment_id INTEGER NOT NULL,
  status TEXT NOT NULL, -- pending | processed | skipped | failed
  reason TEXT,
  processed_at TEXT,
  run_id INTEGER,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  error TEXT,
  PRIMARY KEY (workflow_id, segment_id)
);
```

이 테이블이 “빠짐없이 태운다”의 핵심이다.

v1은 single-writer이므로 `claimed`/lease는 쓰지 않는다. multi-agent 동시 writer가 필요해지는 시점에 v2에서 lease를 도입한다.

`reason`은 enum으로 제한한다.

```text
not_relevant | sensitive | superseded | low_confidence | out_of_scope | duplicate | failed_policy
```

---

### 6.9 Runs

collector와 workflow 실행 이력을 모두 run으로 남긴다.

```sql
CREATE TABLE runs (
  id INTEGER PRIMARY KEY,
  run_type TEXT NOT NULL, -- collect | normalize | workflow
  key TEXT NOT NULL,
  scope_key TEXT,
  input_segment_set_hash TEXT,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  input_json TEXT,
  output_path TEXT,
  error TEXT,
  metadata_json TEXT,
  UNIQUE(run_type, key, scope_key, input_segment_set_hash)
);
```

workflow run은 idempotent해야 한다.

예:

```text
workflow daily_report + 2026-06-15 + 입력 segment hash
```

같은 입력으로 같은 보고서가 중복 생성되지 않게 한다.

---

### 6.10 Run inputs

`run`은 특정 stream의 자식이 아니다.

- collect run은 여러 stream을 입력으로 받을 수 있다.
- normalize run은 여러 item/artifact를 입력으로 받을 수 있다.
- workflow run은 여러 segment를 입력으로 받을 수 있다.

그래서 run의 입력은 별도 테이블로 연결한다.

```sql
CREATE TABLE run_inputs (
  run_id INTEGER NOT NULL,
  input_type TEXT NOT NULL, -- stream | item | artifact | segment | workflow
  input_id INTEGER,
  input_key TEXT,
  role TEXT, -- source | scope | dependency | retry_of
  created_at TEXT NOT NULL
);
```

예:

```text
collect slack run
  input_type=stream, input_id=<slack stream id>

normalize plaud run
  input_type=item, input_id=<plaud recording item id>

workflow daily_report run
  input_type=segment, input_id=<summary segment id>
```

---

### 6.11 Context bundles

Context bundle은 workflow가 output을 만들기 전에 사용하는 **curated input package**다.

Lineage가 “output이 무엇을 근거로 만들어졌는가”를 사후 추적한다면, context bundle은 “output 생성을 위해 어떤 맥락을 의도적으로 포장했는가”를 사전에 기록한다.

```sql
CREATE TABLE context_bundles (
  id INTEGER PRIMARY KEY,
  workflow_id INTEGER,
  run_id INTEGER,
  purpose TEXT NOT NULL, -- draft_reply | daily_report | todo_plan | gbrain_fanout | code_change
  title TEXT,
  selection_policy TEXT, -- deterministic | agent | hybrid
  trust_policy_json TEXT,
  sensitivity_policy_json TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT
);
```

```sql
CREATE TABLE context_bundle_entries (
  bundle_id INTEGER NOT NULL,
  entry_type TEXT NOT NULL, -- segment | artifact | output | actor | trust_assessment | conflict
  entry_id INTEGER NOT NULL,
  role TEXT, -- primary | supporting | counter_evidence | background | excluded_reason
  rank INTEGER,
  created_at TEXT NOT NULL,
  PRIMARY KEY(bundle_id, entry_type, entry_id, role)
);
```

규칙:

- workflow는 raw DB를 임의로 긁기보다 context bundle을 입력으로 받는 것을 권장한다.
- bundle은 output 품질을 높이기 위한 context selection 단위다.
- bundle entry에는 신뢰도와 민감도 정책이 반영되어야 한다.
- output이 생성되면 `lineage`는 bundle에 포함된 핵심 segment와 output을 연결한다.

---

### 6.12 Lineage

결과물이 어떤 segment에서 나왔는지 기록한다.

```sql
CREATE TABLE lineage (
  id INTEGER PRIMARY KEY,
  output_id INTEGER NOT NULL,
  segment_id INTEGER NOT NULL,
  relation TEXT NOT NULL DEFAULT 'based_on', -- based_on | quotes | summarizes | implements
  created_at TEXT NOT NULL,
  UNIQUE(output_id, segment_id, relation)
);
```

---

### 6.13 Schema migrations

Phase가 진행될수록 스키마가 바뀌므로 migration 기록은 v1 필수다.

```sql
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
```

---

### 6.14 Routing audit view

routing되지 않은 segment를 감지하기 위한 view를 둔다.

```sql
CREATE VIEW unrouted_segments AS
SELECT s.*
FROM segments s
WHERE NOT EXISTS (
  SELECT 1 FROM workflow_segment_state wss
  WHERE wss.segment_id = s.id
);
```

이 view가 비어 있지 않으면 doctor/stats에서 경고한다.

---

### 6.15 Outputs

derived 결과물은 기본적으로 다시 workflow 입력으로 쓰지 않는다.

```sql
CREATE TABLE outputs (
  id INTEGER PRIMARY KEY,
  run_id INTEGER NOT NULL,
  context_bundle_id INTEGER,
  output_kind TEXT NOT NULL, -- report | diary | todo_proposal | calendar_proposal | gbrain_update | draft
  output_ref TEXT NOT NULL,
  path TEXT,
  created_at TEXT NOT NULL,
  metadata_json TEXT
);
```

Output에는 사용자 체감 품질을 측정하기 위한 feedback/metric을 붙일 수 있다.

```sql
CREATE TABLE output_feedback (
  id INTEGER PRIMARY KEY,
  output_id INTEGER NOT NULL,
  feedback_type TEXT NOT NULL, -- accepted | rejected | edited | sent_unedited | useful | not_useful
  value TEXT,
  actor TEXT, -- user | workflow | external_system
  created_at TEXT NOT NULL,
  metadata_json TEXT
);
```

```sql
CREATE TABLE output_metrics (
  id INTEGER PRIMARY KEY,
  output_id INTEGER NOT NULL,
  metric_key TEXT NOT NULL, -- draft_delta | time_to_approve | unedited_send | useful_item_count
  metric_value REAL,
  unit TEXT,
  measured_at TEXT NOT NULL,
  metadata_json TEXT,
  UNIQUE(output_id, metric_key)
);
```

---

### 6.16 Drafts

Todo/action 후보가 나온 뒤에는 그에 대한 초안도 관리해야 한다. 초안은 단순 텍스트가 아닐 수 있다.

예:

- Slack/메일 답장 초안: Markdown
- 외부 공유용 문서 초안: HTML
- PR 코멘트 초안: Markdown
- 실행 가능한 자동화 코드: Python/TypeScript/Shell
- 캘린더 초대 문구: text/Markdown

초안은 output의 한 종류지만, 수정/승인/폐기 lifecycle이 따로 있으므로 별도 테이블로 관리한다.

```sql
CREATE TABLE drafts (
  id INTEGER PRIMARY KEY,
  output_id INTEGER,
  draft_type TEXT NOT NULL, -- reply | document | code | calendar_message | todo_plan | other
  format TEXT NOT NULL, -- md | html | txt | py | ts | sh | json | other
  title TEXT,
  path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft', -- draft | reviewed | approved | rejected | superseded | executed
  target_ref TEXT, -- slack channel, email thread, repo path, calendar event, etc.
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);
```

draft row는 논리적 초안이고, 실제 내용은 `draft_versions`가 immutable하게 관리한다. 수정 시 새 draft를 만들지 않고 새 version을 추가한다. draft 자체의 status는 승인/폐기/실행 lifecycle만 나타낸다.

```sql
CREATE TABLE draft_versions (
  id INTEGER PRIMARY KEY,
  draft_id INTEGER NOT NULL,
  version INTEGER NOT NULL,
  path TEXT NOT NULL,
  content_hash TEXT,
  created_at TEXT NOT NULL,
  created_by TEXT,
  change_note TEXT,
  UNIQUE(draft_id, version)
);
```

초안이 어떤 action/todo 후보에서 나왔는지는 별도 링크 테이블이 아니라 `lineage(output_id, segment_id)`로 남긴다.

---
