# Implementation, Scope, and Success Criteria

> Part of the Continuum planning docs. See [planning index](README.md).

## 12. 구현 순서

### Phase 1 — Ledger core

1. `continuum.db` 스키마 생성
2. `schema_migrations` 도입
3. `continuum` CLI skeleton 생성
4. `doctor`, `stats`, `streams list`, `items list` 구현
5. v1 single-writer 실행 락 도입

### Phase 2 — Plaud migration

1. Plaud collector가 `items/artifacts/segments`를 등록하게 수정
2. 기존 `seen-files.json`를 DB item unique constraint로 대체
3. summary/transcript를 immutable segment로 등록
4. source default sensitivity를 적용
5. unrouted segment audit가 동작하는지 검증

### Phase 3 — Workflow state

1. `daily_report`, `morning_report` workflow 등록
2. `pending` 조회 CLI 구현
3. 처리 완료/skip/failed 기록 구현

### Phase 4 — Report integration

1. daily/morning report가 `continuum workflows pending`으로 입력을 받게 수정
2. output lineage 기록
3. report 생성 idempotency 검증

### Phase 4.5 — Agent enrichment / drafts / GBrain

1. `action_candidate`, `event_candidate`, `durable_fact_candidate`, `entity_candidate` segment 도입
2. diary/todo_planner/gbrain_fanout workflow 등록
3. drafts lifecycle 도입
4. GBrain fanout은 durable_candidate segment 중심으로 처리

### Phase 5 — Slack redesign

1. Slack workspace/channel을 stream으로 등록
2. channel cursor 도입
3. message/thread item화
4. unread/activity는 snapshot artifact로만 저장

### Phase 6 — Push support (v2)

1. `continuum ingest-event` 구현
2. `_inbox/webhook-events` raw 저장
3. trigger policy 평가
4. Hermes webhook/cron 연동

v1에서는 구현하지 않고 인터페이스만 보존한다.

---

## 13. 비목표

v1에서 하지 않을 것:

- 완전한 event sourcing framework 만들기
- 모든 source의 완벽한 history versioning
- 자동 todo/calendar write
- GBrain에 모든 raw text 저장
- 외부 queue system 도입
- Dagster/Prefect/Temporal 도입
- push/webhook runtime 구현
- 동적 JSON routing rule engine 완성
- multi-agent lease/claim 동시 처리
- LLM enricher 전체 자동화

SQLite + filesystem + CLI로 충분히 시작한다.

---

## 14. 성공 기준

v1 성공 기준:

1. Plaud 메모가 수집되면 DB에 item/artifact/segment가 생긴다.
2. 같은 Plaud 메모가 중복 수집되지 않는다.
3. daily_report/morning_report가 같은 segment를 각각 독립적으로 pending/processed/skipped 처리할 수 있다.
4. 어떤 report가 어떤 source segment를 읽었는지 lineage로 추적된다.
5. 새 source가 추가되어도 DB 모델을 크게 바꾸지 않는다.
6. Hermes 외부 agent도 CLI로 context를 읽고 output/draft를 제출할 수 있다.
7. workflow output에 대한 최소 feedback/metric을 기록할 수 있다.

v1.5 성공 기준:

1. action/todo 후보에서 생성된 초안이 `drafts`로 저장되고 승인/폐기/수정 이력이 남는다.
2. diary/todo_planner/gbrain_fanout이 candidate segment 기반으로 동작한다.
3. draft/report/proposal output이 context bundle을 입력으로 사용하고, bundle → output → lineage가 추적된다.
4. MCP server가 주요 read/write surface를 제공한다.

Outcome metric 예:

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
- v1은 polling only로 시작하고, push는 v2에서 붙인다.
- 인터페이스는 CLI 중심으로 두어 Hermes 외부 agent도 붙을 수 있게 한다.
---
