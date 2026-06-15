# Data Model

> Part of the Continuum planning docs. See [planning index](README.md).

## Data Model — Core Entities

#### 6.0 용어 기준

엔티티 이름은 다음 기준으로 고정한다.

| 개념 | 의미 | 예 |
|---|---|---|
| `stream` | 수집 가능한 외부 데이터 입구 | Slack 채널, Plaud 계정, Mail inbox |
| `cursor` | stream별 수집 위치 | Slack latest_ts, Mail last_uid |
| `item` | 외부 시스템의 원본 객체 하나 | 메시지 1개, 녹음 1개, 메일 1통 |
| `artifact` | 원본/파생 파일 | transcript.txt, raw.json, audio.mp3 |
| `segment` | workflow가 읽는 최소 처리 단위 | summary, transcript chunk, message |
| `workflow` | segment를 소비하는 사용처 | daily_report, morning_report |
| `workflow_package` | host-agnostic workflow spec | input/output contract, safety policy, guide |
| `run` | collector/normalizer/workflow 실행 1회 | daily_report 2026-06-15 실행 |
| `context_bundle` | output 생성을 위한 curated input package | draft reply용 관련 segment 묶음 |
| `output` | run이 만든 산출물 | report.html, todo proposal, draft |
| `output_feedback` | output에 대한 사용자/시스템 반응 | accepted, edited, useful |
| `output_metric` | output 품질/활용 지표 | draft_delta, unedited_send_rate |
| `lineage` | output의 근거 segment 연결 | report가 읽은 segment 목록 |
| `draft` | 승인/수정/실행 lifecycle이 있는 초안 | 답장 초안, HTML 초안, 코드 초안 |

중요한 구분:

- `cursor`는 **수집 위치**이고, `workflow_segment_state`는 **처리 상태**다.
- `run`은 특정 stream의 자식이 아니다. collect run은 여러 stream을, workflow run은 여러 segment를 입력으로 받을 수 있다. 그래서 `run_inputs`로 입력을 따로 연결한다.
- 외부 시스템은 source이면서 write target일 수 있다. 읽어온 객체는 `item/segment`, 쓰려고 만든 것은 `output/draft/proposal`, 실행 결과는 다음 collect에서 다시 `item/segment`로 reconcile한다.

#### 6.0.1 Source shape와 sync behavior

Source별 전용 모델을 먼저 만들지 않는다. source item의 **primary shape**와 **sync behavior**를 분리한다.

Shape는 source item의 “주된 의미” 기준으로 하나만 선택한다. 시간이 지나며 child가 추가되는지, 수정되는지, version이 생기는지는 shape가 아니라 `sync_behavior`로 표현한다.

| Shape | 정의 | 예시 | 기본 처리 |
|---|---|---|---|
| `append_entry` | 시간순 stream에 추가되는 독립 entry | Slack channel message, Discord message, Telegram message, log line, webhook event | stream cursor + item/segment 생성 |
| `conversation` | 하나의 대화/논의 단위. root와 replies/participants를 가질 수 있음 | Slack thread, Discord thread, Telegram topic, Gmail thread, GitHub issue discussion, Linear issue comments | aggregate item + child sync + summary segment |
| `recording` | 음성/영상처럼 transcript/extraction이 필요한 media record | Plaud recording, Zoom recording, Teams recording, voice memo, call recording | artifact 저장 + transcript/summary segment |
| `scheduled_event` | 시작/종료 시간과 참석자가 있는 일정/회의 객체 | Calendar event, meeting invite, interview schedule, webinar, reservation | time fields + attendees + update sync |
| `task` | 완료/기한/우선순위/상태 전이가 있는 actionable object | Apple Reminder, todo, Linear issue, GitHub issue, Jira ticket, Asana task | state tracking + due/status segment |
| `document` | 사람이 읽는 본문 중심 문서 | PDF, Google Doc, Notion page, Markdown note, proposal doc, email attachment doc | artifact + body/summary segments + version/hash |
| `dataset` | row/record 집합 또는 structured data dump | CSV, spreadsheet, Airtable export, JSONL, database query result | artifact + schema/profile/row summary segments |
| `snapshot` | 특정 시점의 관측 상태. 그 자체가 처리 단위라기보다 상태 사진 | unread inbox listing, Slack channel list, file tree, system status, search result page | artifact 저장 + 필요 시 source_health/summary segment |
| `external_reference` | 원문은 외부에 있고 Continuum에는 포인터/metadata만 있는 객체 | URL bookmark, GitHub PR link, Linear project link, Drive file pointer, web article URL | metadata + fetch/resolve 상태 관리 |

`report`, `diary`, `GBrain update`, `todo proposal`, `draft` 같은 산출물은 source shape가 아니라 **output**으로 관리한다.

예:

| Source object | Shape | sync_behavior 예 |
|---|---|---|
| Slack channel message | `append_entry` | append-only + watermark |
| Slack thread | `conversation` | children_grow |
| Gmail thread | `conversation` | children_grow |
| Calendar event | `scheduled_event` | mutable_record |
| Reminder/todo item | `task` | mutable_record |
| Plaud recording | `recording` | extraction_pending |
| Google Doc | `document` | versioned |
| CSV export | `dataset` | replace_snapshot 또는 versioned |
| Slack unread list | `snapshot` | point_in_time |

같은 shape라도 동기화 방식은 다를 수 있다. 반대로 다른 shape라도 같은 sync behavior를 공유할 수 있다.

| Sync behavior | 의미 | 예시 | 상태 저장 |
|---|---|---|---|
| `append_only` | 새 entry가 뒤에만 붙음 | channel timeline, log stream | `stream_cursors` |
| `watermarked_append` | 늦게 도착한 entry를 잡기 위해 최근 구간 재스캔 | Slack/Discord channel | `stream_cursors` + watermark |
| `children_grow` | 기존 item 아래 child/reply/comment가 추가됨 | Slack thread, Gmail thread, GitHub issue comments | `item_sync_state` |
| `mutable_record` | 같은 외부 id의 필드가 바뀜 | calendar event time change, task status change | item update + 새 segment/supersede |
| `versioned` | 새 버전이 생김 | Google Doc revision, PDF update, code file snapshot | artifact/segment 새 버전 |
| `replace_snapshot` | 매번 전체 상태 사진을 다시 찍음 | inbox listing, channel list, search results | snapshot artifact |
| `extraction_pending` | 원본 수집 후 transcript/OCR/parse가 뒤따름 | Plaud, PDF OCR, meeting recording | artifact + normalize run |

```text
Slack thread = conversation + children_grow
Gmail thread = conversation + children_grow
GitHub issue discussion = conversation + children_grow
Calendar event = scheduled_event + mutable_record
Reminder todo = task + mutable_record
Google Doc = document + versioned
Plaud recording = recording + extraction_pending
```

#### 6.0.2 Source이면서 write target인 시스템

Todo list, Calendar, GBrain, Slack, Mail처럼 Continuum이 읽기도 하고 쓰기도 하는 시스템은 **read path**와 **write path**를 분리한다.

```text
Read path:
external system → connector → stream/item/artifact/segment → workflow

Write path:
workflow → output/draft/proposal → approval → external write → collect/reconcile → item/segment
```

규칙:

- 외부 시스템에 이미 존재하는 객체는 source `item`이다.
- Continuum이 만들고 싶은 변경은 먼저 `output`, `draft`, 또는 proposal 성격의 segment/output이다.
- 외부 write는 승인 가능한 side effect다. write 성공 응답만으로 source truth를 확정하지 않는다.
- 다음 collect에서 외부 시스템의 실제 객체를 다시 읽고, `external_id`로 기존 proposal/output과 reconcile한다.
- lineage는 “어떤 output이 어떤 external item을 만들었거나 수정했는지”를 연결해야 한다.

예: Todo 생성

```text
action_candidate segment
  → todo proposal output/draft
  → user approves
  → Reminders write executes
  → Reminders collector sees external_id
  → task item/segment is created or updated
  → lineage links proposal output ↔ created task item
```

이 모델을 쓰면 todo list가 source이면서 sink여도 충돌하지 않는다. Source 상태는 외부 시스템에서 확인된 사실이고, output/draft는 Continuum이 제안하거나 실행한 의도다.

#### 6.1 Streams

`stream`은 수집 가능한 외부 데이터 입구다.

예:

- `slack:alpaon:#synapus`
- `slack:candid:#0_프로덕트`
- `plaud:account:default`
- `mail:google:inbox`
- `calendar:apple:primary`

```sql
CREATE TABLE streams (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  connector TEXT NOT NULL,
  shape TEXT NOT NULL,
  display_name TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

---

#### 6.2 Stream cursors

cursor는 stream별로 외부 시스템에서 어디까지 가져왔는지 기록한다.

Slack처럼 append 되는 데이터에는 필수다.
Plaud처럼 최근 목록 polling도 `last_seen_created_at`, `last_scan_at` 등을 둔다.

```sql
CREATE TABLE stream_cursors (
  stream_id INTEGER NOT NULL,
  cursor_key TEXT NOT NULL,
  cursor_value TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (stream_id, cursor_key)
);
```

중요: cursor는 **수집 최적화용**이지, 처리 완료의 근거가 아니다.

---

#### 6.3 Items

`item`은 외부에서 들어온 원본 단위다.

예:

- Slack message 1개
- Slack thread 1개
- Plaud recording 1개
- Mail message 1개
- Calendar event 1개
- Reminder 1개

```sql
CREATE TABLE items (
  id INTEGER PRIMARY KEY,
  stream_id INTEGER NOT NULL,
  external_id TEXT NOT NULL,
  item_type TEXT NOT NULL,
  title TEXT,
  occurred_at TEXT,
  collected_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  content_hash TEXT,
  status TEXT NOT NULL DEFAULT 'collected',
  raw_path TEXT,
  metadata_json TEXT,
  UNIQUE (stream_id, external_id)
);
```

---

#### 6.4 Artifacts

큰 파일이나 원문은 artifact로 저장한다.

예:

- `transcript.txt`
- `summary.md`
- `mail_body.txt`
- `slack_raw.json`
- `audio.mp3`

```sql
CREATE TABLE artifacts (
  id INTEGER PRIMARY KEY,
  item_id INTEGER,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  mime_type TEXT,
  content_hash TEXT,
  size_bytes INTEGER,
  created_at TEXT NOT NULL,
  metadata_json TEXT
);
```

---

#### 6.5 Segments

workflow가 실제로 읽는 단위다.

긴 Plaud transcript, 긴 Slack thread, 긴 문서는 segment로 쪼갠다.

```sql
CREATE TABLE segments (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL,
  supersedes_segment_id INTEGER,
  superseded_by_segment_id INTEGER,
  segment_type TEXT NOT NULL,
  ordinal INTEGER NOT NULL DEFAULT 0,
  text_path TEXT,
  text_hash TEXT,
  occurred_at TEXT,
  confidence REAL,
  sensitivity TEXT NOT NULL DEFAULT 'personal',
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (item_id, segment_type, ordinal)
);
```

불변성 규칙:

- `text_path`가 가리키는 내용은 segment 생성 후 수정하지 않는다.
- 내용이 바뀌면 새 segment를 생성하고 기존 segment를 supersede한다.
- workflow가 이미 처리한 segment의 lineage는 당시 시점 스냅샷으로 유지한다.

예:

```text
Plaud recording
  segment 0: summary
  segment 1: transcript chunk 001
  segment 2: transcript chunk 002
  segment 3: action candidates
```

---

---

## Data Model — Workflows, Runs, and Outputs

#### 6.6 Workflows

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
  trigger_policy_json TEXT, -- push/schedule trigger policy
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

---

#### 6.7 Workflow packages

Workflow package는 host-agnostic workflow 정의다.

`workflows` table이 runtime 등록 상태라면, workflow package는 Hermes/Claude Code/Codex/MCP/local cron이 공유할 수 있는 portable spec이다.

```sql
CREATE TABLE workflow_packages (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL,
  version TEXT NOT NULL,
  package_path TEXT NOT NULL,
  input_contract_json TEXT NOT NULL,
  output_contract_json TEXT NOT NULL,
  required_capabilities_json TEXT,
  safety_policy_json TEXT,
  guide_path TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(key, version)
);
```

규칙:

- package는 특정 agent prompt가 아니라 host-agnostic spec이어야 한다.
- host별 adapter는 package를 읽어 자기 실행 방식으로 변환할 수 있다.
- package에는 “무슨 context bundle을 입력으로 받고, 어떤 output을 만들며, 어떤 side effect 권한이 필요한지”가 명시되어야 한다.

---

#### 6.8 Workflow state

각 workflow가 각 segment를 어떻게 처리했는지 기록한다.

```sql
CREATE TABLE workflow_segment_state (
  workflow_id INTEGER NOT NULL,
  segment_id INTEGER NOT NULL,
  status TEXT NOT NULL, -- pending | claimed | processed | skipped | failed
  reason TEXT,
  claim_owner TEXT,
  claim_expires_at TEXT,
  processed_at TEXT,
  run_id INTEGER,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  error TEXT,
  PRIMARY KEY (workflow_id, segment_id)
);
```

이 테이블이 “빠짐없이 태운다”의 핵심이다.

초기 runtime은 single-writer로 운영할 수 있지만, 스키마와 상태 모델은 multi-agent claim/lease까지 포함한다. 단일 writer는 `claimed`를 생략하고 `pending → processed/skipped/failed`로 처리할 수 있다. 여러 worker가 붙으면 `pending → claimed(owner, expires_at) → processed/skipped/failed` 흐름을 사용한다.

`reason`은 enum으로 제한한다.

```text
not_relevant | sensitive | superseded | low_confidence | out_of_scope | duplicate | failed_policy
```

---

#### 6.9 Runs

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

#### 6.10 Run inputs

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

#### 6.11 Context bundles

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

#### 6.12 Lineage

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

#### 6.13 Schema migrations

Phase가 진행될수록 스키마가 바뀌므로 migration 기록은 필수다.

```sql
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
```

---

#### 6.14 Routing audit view

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

#### 6.15 Outputs

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

#### 6.16 Drafts

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

---

## Data Model — Actors and Trust

#### 6.17 Item sync state

일부 source item은 시간이 지나며 child/update/version이 추가되는 aggregate다.

stream cursor는 새 top-level item을 찾는 데 필요하지만, 이미 발견한 item 내부의 child 증가나 update/version 변화까지 추적하기에는 부족하다. 그래서 item별 sync state를 둔다.

```sql
CREATE TABLE item_sync_state (
  item_id INTEGER NOT NULL,
  sync_kind TEXT NOT NULL, -- children_grow | mutable_record | versioned | extraction_pending
  cursor_value TEXT,
  count_seen INTEGER,
  latest_child_external_id TEXT,
  latest_child_occurred_at TEXT,
  last_checked_at TEXT,
  last_full_sync_at TEXT,
  stale_after TEXT,
  metadata_json TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY(item_id, sync_kind)
);
```

예:

```text
conversation item
  sync_kind = children_grow
  cursor_value = latest_child_cursor
  count_seen = child_count_seen
  latest_child_occurred_at = latest child timestamp
```

Source-specific mapping examples:

```text
Slack thread
  sync_kind = children_grow
  cursor_value = latest_reply_ts
  count_seen = reply_count_seen

Gmail thread
  sync_kind = children_grow
  cursor_value = latest_message_id or internal_date
  count_seen = message_count_seen

Google Doc
  sync_kind = versioned
  cursor_value = latest_revision_id

Calendar event
  sync_kind = mutable_record
  cursor_value = updated_at / etag
```

규칙:

- `stream_cursors`는 stream-level 수집 위치다.
- `item_sync_state`는 item-level aggregate 내부 동기화 위치다.
- Slack thread, mail thread, calendar event update, document version처럼 “원본 item이 계속 자라는 경우”에 쓴다.
- item_sync_state는 mutable state이며, 근거 데이터는 아니다.

---

#### 6.18 Source actors

Provenance-first 원칙상 “어느 소스에서 왔는가”뿐 아니라 “어떤 사람/계정이 관련됐는가”도 추적해야 한다.

source actor는 Slack user, email address, calendar attendee, Plaud speaker처럼 외부 source 안에서 식별되는 사람/계정이다.

```sql
CREATE TABLE source_actors (
  id INTEGER PRIMARY KEY,
  source_system TEXT NOT NULL, -- slack | mail | calendar | plaud | telegram | discord
  external_actor_id TEXT NOT NULL,
  display_name TEXT,
  handle TEXT,
  email TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_system, external_actor_id)
);
```

item과 actor의 관계는 source마다 다르므로 링크 테이블로 둔다.

```sql
CREATE TABLE item_actor_links (
  item_id INTEGER NOT NULL,
  actor_id INTEGER NOT NULL,
  role TEXT NOT NULL, -- author | sender | recipient | attendee | mentioned | speaker | owner
  created_at TEXT NOT NULL,
  PRIMARY KEY(item_id, actor_id, role)
);
```

규칙:

- actor는 source-local identity다. 사람 통합/동명이인 해결은 core가 강제하지 않는다.
- “김지섭 Slack user”와 “김지섭 Gmail address”를 같은 사람으로 묶는 것은 별도 enrichment 또는 상위 application layer가 한다.
- core는 source actor를 보존하고, output/lineage에서 추적 가능하게 만드는 것까지만 책임진다.

---

#### 6.19 Evidence trust

Provenance-first는 단순히 “출처를 남긴다”가 아니라, **근거의 신뢰도와 충돌 관계를 관리한다**는 뜻이다.

신뢰도는 처음 들어올 때 선평가될 수 있고, 나중에 더 강한 근거/사용자 확인/반박으로 후평가될 수 있다.

```sql
CREATE TABLE evidence_trust_assessments (
  id INTEGER PRIMARY KEY,
  target_type TEXT NOT NULL, -- item | artifact | segment | output | actor | stream
  target_id INTEGER NOT NULL,
  assessment_phase TEXT NOT NULL, -- pre | post
  trust_score REAL, -- 0.0 ~ 1.0
  trust_level TEXT, -- low | medium | high | verified | disputed
  basis TEXT NOT NULL, -- source_default | actor_reputation | user_confirmed | cross_checked | contradicted | stale
  assessed_by TEXT NOT NULL, -- deterministic_worker | user | agent | external_system
  run_id INTEGER,
  note TEXT,
  created_at TEXT NOT NULL
);
```

충돌하는 정보도 별도 관계로 남긴다.

```sql
CREATE TABLE evidence_conflicts (
  id INTEGER PRIMARY KEY,
  left_type TEXT NOT NULL,
  left_id INTEGER NOT NULL,
  right_type TEXT NOT NULL,
  right_id INTEGER NOT NULL,
  conflict_type TEXT NOT NULL, -- contradicts | supersedes | duplicates | weakly_disagrees
  resolution_status TEXT NOT NULL DEFAULT 'unresolved', -- unresolved | resolved | ignored
  preferred_type TEXT,
  preferred_id INTEGER,
  reason TEXT,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);
```

규칙:

- source/stream/actor별 기본 신뢰도는 선평가로 들어간다.
- 사용자 확인, 교차검증, 더 강한 원본 발견은 후평가로 들어간다.
- 모순된 정보가 있으면 output 생성 시 더 높은 trust를 우선하되, 충돌 사실 자체를 숨기지 않는다.
- trust는 core가 “정답”을 강제하는 값이 아니라, application layer가 판단할 수 있게 제공하는 근거 metadata다.

---
