# Data Model — Core Entities

> Part of the Continuum planning docs. See [planning index](README.md).

### 6.0 용어 기준

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

### 6.1 Streams

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

### 6.2 Stream cursors

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

### 6.3 Items

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

### 6.4 Artifacts

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

### 6.5 Segments

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
