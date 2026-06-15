# Implementation, Scope, and Success Criteria

> Part of the Continuum planning docs. See [planning index](README.md).

## 12. 구현 순서

Continuum은 아래 capability를 모두 구현 대상에 포함한다. 다만 안정적인 순서로 쌓기 위해 phase를 나눈다.

### Phase 1 — Ledger core + CLI foundation

1. `continuum.db` 스키마 생성
2. `schema_migrations` 도입
3. `continuum` CLI skeleton 생성
4. `setup`, `init`, `doctor`, `stats`, `streams list`, `items list` 구현
5. runtime path/config 관리 구현
6. single-writer 실행 락 도입

### Phase 2 — Core source ingestion

1. Plaud collector가 `items/artifacts/segments`를 등록하게 수정
2. Slack workspace/channel을 stream으로 등록
3. Slack channel cursor 도입
4. Slack message/thread item화
5. summary/transcript/message/thread_summary를 immutable segment로 등록
6. source default sensitivity를 적용
7. unread/activity는 snapshot artifact로 저장
8. late-arrival watermark 재스캔 구현

### Phase 3 — Workflow queue + routing

1. `daily_report`, `morning_report`, `diary`, `todo_planner`, `calendar_planner`, `gbrain_fanout` workflow 등록
2. `workflow_segment_state` pending/claimed/processed/skipped/failed 구현
3. static routing rule + materialized pending queue 구현
4. unrouted segment audit view와 `doctor/stats` 경고 구현
5. claim/lease CLI 구현
6. 처리 완료/skip/failed/retry 기록 구현

### Phase 4 — Outputs, lineage, context bundles, feedback

1. `context_bundles`, `context_bundle_entries` 구현
2. `outputs`, `output_feedback`, `output_metrics` 구현
3. `lineage` 기록 구현
4. daily/morning report가 pending queue + context bundle을 입력으로 사용하게 수정
5. report 생성 idempotency 검증
6. output feedback/metric 기록 CLI 구현

### Phase 5 — Agent enrichment / drafts / GBrain

1. `action_candidate`, `event_candidate`, `durable_fact_candidate`, `entity_candidate` segment 도입
2. enricher pipeline 구현
3. drafts lifecycle 도입
4. diary/todo_planner/calendar_planner/gbrain_fanout workflow 구현
5. GBrain fanout은 durable_candidate/entity_candidate segment 중심으로 처리
6. approval 기반 external side effect 실행 모델 구현

### Phase 6 — Push/webhook + trigger policy

1. `inbound_events` 테이블 구현
2. `continuum ingest-event` 구현
3. `_inbox/webhook-events` raw 저장
4. trigger policy 평가 구현
5. Hermes webhook/cron 연동
6. polling과 push가 같은 item/segment/routing 모델로 합류하는지 검증

### Phase 7 — MCP server + host integrations

1. `continuum mcp serve` 구현
2. read tools: search/get/list pending/context bundle/lineage
3. write tools: create context bundle, submit output, submit draft, record feedback
4. approval state가 필요한 write/execute tool guardrail 구현
5. Hermes skill과 MCP registration UX 구현
6. Claude/Codex 등 다른 host integration guide 작성

### Phase 8 — Daemon / scheduler / watcher

1. `continuum daemon` 구현
2. local scheduler 구현
3. file watcher/manual drop watcher 구현
4. queue worker와 claim/lease heartbeat 구현
5. daemon health/log/doctor 통합
6. launchd/systemd user service 등록 UX 구현

### Phase 9 — Advanced sync + dynamic routing

1. Slack edit/delete tombstone 정교화
2. thread summary supersede와 child sync 재처리 구현
3. dynamic JSON routing rule engine 구현
4. source별 backfill 전략 구현
5. multi-device/sync-compatible runtime 전략 검증

---

## 13. Core가 직접 책임지지 않는 것

아래는 “안 한다”가 아니라 **Continuum core가 직접 책임지지 않는 것**이다.

- 모든 외부 서비스의 API 한계를 넘어선 완벽한 과거 복원
- 사용자 승인 없는 고위험 write/execute
- GBrain을 raw archive로 사용하는 것
- source/workflow별 제품 정책을 core schema에 박는 것
- 특정 agent host에만 종속되는 workflow 정의
- provenance/lineage/trust 없이 생성되는 opaque output

---

## 14. 성공 기준

### Core success criteria

1. Plaud/Slack/Mail/Calendar/Reminder 등 등록된 source에서 item/artifact/segment가 생성된다.
2. 같은 외부 객체가 중복 수집되지 않는다.
3. 수정/삭제/추가 reply는 item 상태와 새 immutable segment/supersede로 표현된다.
4. workflow별 pending/claimed/processed/skipped/failed 상태가 분리된다.
5. routing되지 않은 segment와 failed workflow state가 doctor/stats에 드러난다.
6. 어떤 output이 어떤 source segment/context bundle에서 나왔는지 lineage로 추적된다.
7. output에 대한 accepted/rejected/edited/executed feedback과 metric을 기록할 수 있다.
8. context bundle → output → lineage 경로가 재현 가능하다.
9. candidate segment 기반 diary/todo/calendar/GBrain workflow가 동작한다.
10. external side effect는 proposal/draft와 approval state를 거쳐 실행된다.
11. CLI와 MCP가 같은 service/domain layer를 호출한다.
12. MCP server가 주요 read/write surface를 제공한다.
13. daemon 없이도 CLI/cron 기반 운영이 가능하고, daemon을 켜면 scheduler/watcher/worker가 동작한다.
14. 새 source가 추가되어도 DB 모델을 크게 바꾸지 않는다.
15. Hermes뿐 아니라 다른 agent도 context를 읽고 output/draft/feedback을 제출할 수 있다.

### Outcome metric 예

| Output | Metric |
|---|---|
| draft | accepted rate, rejected rate, edit distance/draft delta, unedited send rate |
| report | useful item count, dismissed item count, missing item feedback |
| todo/calendar proposal | approved rate, modified-before-approval rate, time-to-approval |
| code draft | executed rate, test pass rate, user edit delta |

---

## 15. 최종 요약

Continuum은 개인 맥락의 SSOT다.

- 파일 저장소가 아니라 ledger다.
- cursor만으로는 부족하고 item/segment/workflow state가 필요하다.
- Slack 같은 append stream은 cursor로 수집하고 item/segment로 처리한다.
- Plaud 같은 긴 녹음은 recording item + transcript/summary segments로 처리한다.
- workflow별 읽음 상태를 분리해야 “빠짐없이 태운다”가 가능하다.
- polling과 push는 모두 같은 item/segment/routing 모델로 합류해야 한다.
- CLI, MCP, daemon은 같은 core service layer의 서로 다른 surface다.
- Hermes뿐 아니라 다른 agent도 Continuum에 붙을 수 있어야 한다.
