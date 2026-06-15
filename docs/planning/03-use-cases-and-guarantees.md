# Use Cases and Guarantees

> Part of the Continuum planning docs. See [planning index](README.md).

## Use Cases and Guarantees

### 10. 사용사례 검토

#### 10.1 일일 보고

- 대상: 전날 발생한 모든 relevant segment
- 처리 기준: `occurred_at` 기준 date range
- consumer state: daily_report가 읽은 segment를 processed/skipped 처리
- lineage: report.html이 어떤 segment에서 나왔는지 기록

애매한 점:
- 일일 보고가 모든 transcript chunk를 다 읽어야 하는가?
- 답: 아니다. `summary`, `action_candidate`, `entity_candidate`를 우선 읽고, 필요 시 transcript chunk로 drill-down한다.

---

#### 10.2 아침 보고

- 대상: 오늘 일정, 미처리 task, 밤사이 새 메시지/메일/녹음
- 처리 기준: since last morning report + today calendar
- push trigger 가능: urgent segment 발생 시 morning report와 별개로 interrupt workflow

애매한 점:
- daily_report와 중복 처리되는가?
- 답: 중복 가능. 그래서 workflow별 state가 필요하다. 같은 segment를 두 workflow가 각각 읽을 수 있다.

---

#### 10.3 일기 작성

- 대상: Plaud 독백, 하루 회고, 개인적 Slack/세션 요약
- 강한 필터 필요: 모든 업무 메시지를 일기에 넣으면 안 됨
- workflow rule이 중요함

애매한 점:
- 일기는 자동 저장해도 되는가?
- 답: 기본은 draft까지만 생성한다. 사용자가 승인하면 저장한다.

---

#### 10.4 Todo / Calendar 조율

- 대상: action_candidate segment
- output: proposed todo/calendar event
- 실제 생성은 승인 기반
- 관련 초안은 `drafts`에 저장

초안 예:

```text
action_candidate: "영근님에게 R4 일정 확인"
  ↓
draft(reply, md): Slack 답장 초안
draft(calendar_message, md): 캘린더 초대 설명문
draft(code, py): 자동 정리 스크립트 초안
```

애매한 점:
- 자동으로 Reminders/Calendar에 쓰면 위험함
- 답: 기본은 `proposal + draft` 생성까지만 한다. write/execute는 별도 승인 필요.

---

#### 10.5 GBrain 맥락 저장

- 대상: durable fact, relationship, decision, timeline event
- raw를 전부 넣으면 안 됨
- gbrain_fanout은 skipped가 정상적으로 많아야 함

애매한 점:
- “읽었지만 저장 안 함”도 처리 완료인가?
- 답: 그렇다. `skipped(reason='not_durable')`로 기록한다.

---

### 11. 아키텍처 보강

#### 11.1 Continuum이 보장하는 것과 보장하지 않는 것

Continuum의 핵심 보장은 “모든 workflow가 모든 데이터를 의미 있게 처리한다”가 아니다.

Continuum이 보장하는 것:

1. 어떤 맥락이 들어왔는지 기록한다.
2. 그 맥락이 어떤 artifact/segment로 분해됐는지 기록한다.
3. 각 workflow가 해당 segment를 처리했는지, 건너뛰었는지, 실패했는지 기록한다.
4. 결과물이 어떤 segment에서 나왔는지 추적한다.

Continuum이 보장하지 않는 것:

1. 외부 source의 과거 데이터를 100% 복원하는 것
2. agent가 항상 정확하게 중요도를 판단하는 것
3. 모든 raw text를 모든 workflow가 읽는 것
4. 사용자 승인 없이 캘린더/투두/GBrain을 완전 자동 변경하는 것

따라서 “누락 없음”의 의미는 다음과 같이 정의한다.

```text
누락 없음 = relevant segment가 workflow queue에 들어가고,
          workflow가 processed/skipped/failed 중 하나의 명시적 상태를 남기는 것
```

---

#### 11.2 Segment routing

모든 segment를 모든 workflow에 넣으면 소음이 폭발한다. 초기 구현부터 routing layer가 필요하다.

```sql
CREATE TABLE routing_rules (
  id INTEGER PRIMARY KEY,
  workflow_id INTEGER NOT NULL,
  match_json TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

예:

```json
{
  "segment_types": ["summary", "action_candidate"],
  "shapes": ["recording", "conversation"],
  "min_confidence": 0.6
}
```

routing 결과는 `workflow_segment_state`에 `pending`으로 materialize한다.
즉 workflow는 매번 전체 DB를 검색하지 않고, 자기 pending queue만 읽는다.

---

#### 11.3 Claim / lease 모델

Claim/lease는 multi-agent 동시 처리와 long-running worker를 위한 필수 queue capability다. 초기에는 single-writer 운영으로 시작할 수 있지만, 상태 모델과 CLI는 claim/lease를 포함한다.

```sql
ALTER TABLE workflow_segment_state ADD COLUMN claim_owner TEXT;
ALTER TABLE workflow_segment_state ADD COLUMN claim_expires_at TEXT;
```

처리 흐름:

```text
pending → claimed(owner, expires_at) → processed/skipped/failed
```

lease가 만료되면 다시 pending으로 돌릴 수 있다.

CLI:

```bash
continuum workflows claim daily_report --limit 20 --owner hermes
continuum workflows complete daily_report <segment_id> --run <run_id>
continuum workflows skip daily_report <segment_id> --reason not_relevant
```

---

#### 11.4 Normalization과 enrichment를 분리

collector가 바로 “중요한 일”을 판단하면 안 된다.

- collector: 외부 시스템에서 가져오고 raw/artifact/item 생성
- normalizer: source별 raw를 canonical segment로 변환
- enricher: action/durable/entity 후보 생성
- workflow: 목적별 처리

```text
collect → normalize → enrich → route → workflow
```

예: Plaud

```text
recording item
  ↓ normalize
summary segment + transcript chunks
  ↓ enrich
action_candidate + durable_fact_candidate + entity_candidate
  ↓ route
morning_report / diary / gbrain_fanout / todo_planner
```

---

#### 11.5 Segment type 표준

기본 segment type:

| Segment type | 의미 | 주 사용처 |
|---|---|---|
| `body` | 원문 본문 | drill-down |
| `summary` | 짧은 요약 | report |
| `transcript_chunk` | 긴 transcript 조각 | deep analysis |
| `message` | 개별 메시지 | report |
| `thread_summary` | thread 요약 | report |
| `source_health` | 수집 상태/오류 | report/system health |

candidate segment type:

| Segment type | 의미 | 주 사용처 |
|---|---|---|
| `action_candidate` | 할 일 후보 | todo/calendar planner |
| `event_candidate` | 일정 후보 | calendar planner |
| `durable_fact_candidate` | 장기 기억 후보 | gbrain_fanout |
| `entity_candidate` | 사람/회사/프로젝트 후보 | gbrain_fanout |

---

#### 11.6 Confidence와 sensitivity

workflow routing에는 중요도뿐 아니라 민감도도 필요하다.

```sql
ALTER TABLE segments ADD COLUMN confidence REAL;
ALTER TABLE segments ADD COLUMN sensitivity TEXT; -- public | personal | confidential | secret
```

규칙:

- `secret`은 report/GBrain 기본 대상에서 제외
- `confidential`은 요약만 허용, raw link 노출 금지
- `personal`은 diary에는 허용, public report에는 제외 가능
- `public`은 일반 처리 가능

이 기준이 없으면 magic link, 보안 메일, 민감 회의록이 보고서/GBrain에 새어 나갈 수 있다.

---

#### 11.7 Push event inbox

push는 즉시 처리하되, 먼저 raw event를 안전하게 저장한다.

```sql
CREATE TABLE inbound_events (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  event_type TEXT NOT NULL,
  external_event_id TEXT,
  received_at TEXT NOT NULL,
  payload_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received',
  error TEXT,
  UNIQUE(source, external_event_id)
);
```

흐름:

```text
webhook → inbound_events(received) → connector adapter → item/segment → route → workflow queue
```

즉 push도 DB 관점에서는 polling과 같은 item/segment 모델로 합류한다.

---

#### 11.8 가능한 use-case / 어려운 use-case

가능한 use-case:

| Use-case | 조건 |
|---|---|
| Plaud 자동 수집 | file_id dedupe + transcript/summary artifact |
| Slack incremental ingest | channel cursor + message/thread item화 |
| 일일/아침 보고 | workflow별 pending queue + lineage |
| 일기 draft | personal segment routing + 승인 기반 저장 |
| Todo 후보 추출 | action_candidate segment |
| Calendar 후보 추출 | event_candidate segment |
| GBrain fanout | durable_fact/entity candidate + skipped reason |
| 외부 agent 연동 | CLI/MCP read + output/draft 제출 + claim/complete |
| push trigger | inbound_events + routing_rules |

어려운 use-case:

| Use-case | 이유 | 대응 |
|---|---|---|
| 모든 source 과거 전체 복원 | API/권한/삭제 제한 | best-effort backfill |
| 완전 자율 todo/calendar write | side effect 위험 | proposal + 승인 |
| raw 전체 GBrain 저장 | 지식 오염/민감정보 위험 | durable candidate만 |
| Slack 전체 맥락 완벽 이해 | thread/채널 맥락 큼 | segment + drill-down |
| LLM 없는 완전 결정론적 중요도 판단 | 의미 판단 필요 | enricher는 agent/hybrid |
| push-only 운영 | 많은 개인 도구가 webhook 없음 | polling+push hybrid |

---

#### 11.9 반드시 피할 함정

1. source별 전용 테이블을 많이 만들지 않는다.
2. workflow가 raw 파일을 직접 스캔하게 두지 않는다.
3. cursor를 처리 완료 상태로 착각하지 않는다.
4. 모든 segment를 모든 workflow에 넣지 않는다.
5. `processed`만 성공으로 보지 않는다. `skipped`도 명시적 성공이다.
6. GBrain을 raw archive로 쓰지 않는다.
7. 자동 side effect는 proposal 단계 없이 바로 실행하지 않는다.

---
