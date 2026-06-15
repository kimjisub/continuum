# Data Model — Actors and Trust

> Part of the Continuum planning docs. See [planning index](README.md).

### 6.17 Item sync state

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

### 6.18 Source actors

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

### 6.19 Evidence trust

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
