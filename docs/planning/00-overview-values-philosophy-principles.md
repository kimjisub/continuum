# Overview, Values, Philosophy, Principles

> Part of the Continuum planning docs. See [planning index](README.md).

# Continuum 기획서

> 작업명: **Continuum**
> 한 줄 정의: **모든 맥락을 수집하고, 누락 없이 사용자의 워크플로우에 태우는 개인 맥락 운영체제**

---

## 1. 왜 Continuum인가

Continuum은 사용자의 맥락이 끊기지 않고 흐르는 하나의 연속체라는 의미다.

우리가 원하는 가치는:

> 사용자의 모든 맥락을 계속 수집하고, 각 워크플로우가 빠짐없이 읽고, 처리 결과와 근거까지 추적하는 SSOT.

이 이름이 적합한 이유:

- 끊기지 않는 맥락의 흐름을 표현한다.
- 특정 source나 workflow에 묶이지 않는 추상화 계층을 뜻한다.
- Hermes뿐 아니라 다른 agent, local script, MCP server도 붙을 수 있는 중립적 core를 지향한다.
- 단순 저장소가 아니라 stream, ledger, workflow hub에 가까운 시스템을 나타낸다.

---

## 2. 가치 — 왜 이 제품이 필요한가

여기서 **가치**는 구현 방식이나 설계 취향이 아니라, 사용자가 Continuum을 통해 실제로 얻게 되는 결과다.
따라서 “SQLite를 쓴다”, “MCP를 지원한다”, “agent-neutral하다”는 가치가 아니라 그 가치를 만들기 위한 수단이다.

Continuum의 가치는 네 가지다.

1. **맥락이 끊기지 않는다**
   - Slack, Plaud, Mail, Calendar, Reminder, 브라우저, 세션, 파일, 직접 입력 등 흩어진 맥락이 하나의 연속된 기록으로 남는다.
   - 사용자는 “그 얘기가 어디 있었더라?”를 매번 source별로 다시 뒤지지 않아도 된다.
   - agent나 도구가 바뀌어도 사용자의 맥락 자산은 사라지지 않는다.

2. **중요한 맥락이 조용히 묻히지 않는다**
   - relevant context는 적절한 workflow queue에 올라가고, 처리/스킵/실패 중 하나의 상태를 남긴다.
   - 성공은 “모든 raw text를 다 읽었다”가 아니라 “필요한 맥락이 누락 없이 처리 경로에 탔다”이다.
   - 놓친 것이 있으면 사용자가 확인할 수 있어야 한다.

3. **결과물의 근거를 설명할 수 있다**
   - 보고서, 초안, todo/calendar proposal, GBrain 후보가 어떤 source/item/segment/context bundle을 근거로 나왔는지 추적된다.
   - 잘못된 결과가 나오면 “LLM이 그렇게 말했다”가 아니라 어떤 입력과 어떤 판단 경로가 문제였는지 되짚을 수 있다.
   - 신뢰도, 민감도, 충돌 관계가 결과물과 함께 남는다.

4. **사용자가 실제로 더 나은 결정을 하고 일을 끝낸다**
   - Continuum은 처리 상태를 남기는 데서 끝나지 않고, output이 실제로 유용했는지 본다.
   - report는 알아야 할 일을 드러내고, draft는 수정 부담을 줄이고, proposal은 승인 가능한 행동으로 이어져야 한다.
   - 그래서 process metric과 별도로 accepted/rejected/edited/executed 같은 outcome metric을 남긴다.

---

## 2.5 철학 — 무엇을 믿고 어떤 방향을 선택하는가

여기서 **철학**은 개별 규칙 목록이 아니라, Continuum이 반복해서 선택해야 하는 trade-off의 방향이다.
철학은 “왜 그런 설계를 택하는가”를 설명하고, 원칙은 그 철학을 구현할 때 지킬 판단 기준이다.

Continuum의 철학은 다음과 같다.

### 2.5.1 맥락은 agent의 기억이 아니라 사용자의 자산이다

Continuum은 특정 agent, 특정 앱, 특정 모델의 memory가 아니다.
사용자의 맥락은 사용자 소유의 중립 core에 남아야 하며, Hermes, Claude Code, Codex, Gemini, local script, MCP server, custom agent는 모두 그 core를 읽고 쓰는 consumer/producer일 뿐이다.

이 철학이 의미하는 것:

- agent가 바뀌어도 맥락, 처리 상태, lineage, trust/sensitivity 평가는 유지된다.
- core는 특정 host의 prompt나 memory 기능에 종속되지 않는다.
- CLI와 MCP는 surface일 뿐이고, 실제 판단과 상태는 공통 domain/service layer에 남는다.

### 2.5.2 기록보다 해석이 먼저가 아니라, 근거 있는 해석이 먼저다

Continuum은 “좋은 요약”보다 “근거를 설명할 수 있는 요약”을 우선한다.
모든 output은 어떤 source에서 왔고, 어떤 actor와 관련 있고, 어떤 segment/context bundle을 근거로 삼았는지 설명 가능해야 한다.

이 철학이 의미하는 것:

- provenance, lineage, trust, sensitivity는 부가기능이 아니라 core다.
- 모순된 정보는 덮어쓰지 않고 conflict로 남긴다.
- 최신 정보가 항상 정답은 아니며, 더 강한 근거가 우선될 수 있다.

### 2.5.3 자동화는 사람을 대체하기보다 승인 가능한 선택지를 만든다

Continuum의 기본 자동화 단계는 `observe → propose/draft → approve → execute`다.
외부 시스템에 영향을 주는 write/execute는 처음부터 완전 자동화하지 않는다.

이 철학이 의미하는 것:

- todo 생성, calendar write, Slack/메일 전송, GBrain 저장, 코드 실행은 기본적으로 proposal/draft를 먼저 만든다.
- 충분히 검증된 낮은 위험 작업만 trusted rule로 승격한다.
- 위험도가 높을수록 더 명시적인 승인과 더 강한 lineage가 필요하다.

### 2.5.4 core는 얇고 안정적이어야 하며, 풍부함은 edge에서 나온다

Continuum core는 모든 제품 정책을 품은 거대한 앱이 아니다.
core는 맥락을 수집·정규화·라우팅·추적하는 substrate이고, 실제 사용 정책은 source adapter와 workflow/application edge에서 발전한다.

이 철학이 의미하는 것:

- Slack/Plaud/Mail/Calendar별 특수 정책은 adapter/guide로 밀어낸다.
- daily report, diary, todo planner, gbrain fanout의 제품 판단은 workflow edge가 담당한다.
- core가 비대해지면 agent-neutral, inspectable, portable한 성격이 깨진다.

### 2.5.5 로컬에서 설명 가능해야 확장도 가능하다

Continuum은 처음부터 분산 orchestration이나 외부 queue를 전제로 하지 않는다.
먼저 local-first, inspectable, recoverable하게 만들고, 그 위에 sync/cloud/multi-device를 붙일 수 있는 구조를 유지한다.

이 철학이 의미하는 것:

- 사람이 SQLite, filesystem, CLI로 상태를 점검하고 복구할 수 있어야 한다.
- 재처리와 디버깅이 가능하도록 run/input/output/lineage를 남긴다.
- protocol surface는 MCP를 1급 지원하되, 운영 가능한 CLI를 버리지 않는다.

---

## 3. 원칙 — 설계와 구현에서 지킬 판단 기준

여기서 **원칙**은 철학을 실제 설계로 옮길 때 적용하는 구체적 판단 기준이다.
원칙은 “좋은 말”이 아니라 스키마, worker, CLI/MCP, workflow 구현에서 위반 여부를 판정할 수 있어야 한다.

### 3.1 데이터 모델링 원칙

#### 3.1.1 Source 이름보다 data shape을 먼저 본다

“Slack 전용”, “Plaud 전용” 모델을 만들지 않는다. 대신 source item의 **primary shape**와 **sync behavior**를 분리해 추상화한다.

##### Shape는 MECE하게 정의한다

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
| Plaud recording | `recording` | extraction_pending |
| Google Doc | `document` | versioned |
| CSV export | `dataset` | replace_snapshot 또는 versioned |
| Slack unread list | `snapshot` | point_in_time |

##### Sync behavior는 shape와 분리한다

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

이렇게 나누면 Slack thread는 Slack 전용 모델이 아니라 `conversation + children_grow`의 한 예시가 된다.

```text
Slack thread = conversation + children_grow
Gmail thread = conversation + children_grow
GitHub issue discussion = conversation + children_grow
Calendar event = scheduled_event + mutable_record
Google Doc = document + versioned
Plaud recording = recording + extraction_pending
```



#### 3.1.2 원본/근거는 immutable, 상태는 mutable로 분리한다

- artifact/segment/output/lineage는 덮어쓰지 않는다.
- cursor/workflow state/draft status처럼 현재 상태를 나타내는 값만 update한다.
- 수정/재생성은 새 row와 supersede/version으로 표현한다.

#### 3.1.3 출처, 신뢰도, 민감도는 처음부터 함께 저장한다

- provenance는 나중에 붙이는 설명이 아니라 데이터의 일부다.
- sensitivity는 LLM 판단 이전 ingest 시점에 보수적으로 부여한다.
- trust와 sensitivity는 분리한다. 믿을 만한 정보라도 민감할 수 있고, 공개 정보라도 신뢰도가 낮을 수 있다.

#### 3.1.4 derived output은 기본적으로 다시 routing input이 아니다

- report/diary/todo proposal이 다시 입력으로 순환하면 맥락 오염과 중복 판단이 생긴다.
- output을 재입력으로 쓰려면 명시적 workflow rule과 lineage가 필요하다.

### 3.2 처리/운영 원칙

1. **Deterministic-first**
   - cursor, dedupe, hash, schema migration, status update, routing materialization처럼 결정론적으로 가능한 일은 deterministic worker가 한다.
   - LLM/agent는 의미 판단, 요약, 초안 작성처럼 비결정론적 판단이 필요한 곳에만 쓴다.

2. **Explicit state over implicit memory**
   - agent가 “읽었을 것이다”에 기대지 않는다.
   - pending/processed/skipped/failed를 DB에 남긴다.
   - skipped도 정상적인 완료 상태다.

3. **Failure-visible**
   - 수집 실패, 권한 부족, routing 실패, workflow 실패, trust conflict, stale data는 조용히 묻히면 안 된다.
   - unrouted segment와 failed workflow state는 doctor/stats에서 보여야 한다.

4. **Idempotent and replayable**
   - 같은 입력을 다시 처리해도 중복 산출물이 생기지 않아야 한다.
   - run/input/output/lineage를 남겨 재처리와 디버깅이 가능해야 한다.

5. **Context bundle을 output 생성 입력의 단위로 삼는다**
   - output 생성자가 어떤 segment/artifact/trust/conflict/preference를 참고했는지 bundle로 남긴다.
   - “agent가 알아서 읽은 것”은 재현 가능한 입력이 아니다.

6. **Outcome metric을 process metric과 분리한다**
   - `processed/skipped/failed`는 누락 방지 metric이다.
   - accepted/rejected/edited/executed/time_to_approval 같은 값은 사용자 체감 품질 metric이다.
   - 둘 중 하나만 있으면 시스템 품질을 착각한다.

### 3.3 인터페이스/확장 원칙

1. **Core logic은 CLI/MCP 밖에 둔다**
   - CLI와 MCP는 같은 service/domain layer를 호출한다.
   - 어느 한 surface에만 business logic이 있으면 agent-neutral이 깨진다.

2. **MCP는 agent 통합의 1급 surface다**
   - 외부 agent가 Continuum을 subprocess hack으로만 쓰게 만들지 않는다.
   - MCP tool은 초기에는 read-only + output/draft/context bundle 제출 중심으로 시작한다.
   - write/execute성 tool은 approval state를 요구한다.

3. **Workflow는 portable package로 정의한다**
   - workflow 정의를 특정 host의 prompt나 cron job에 가두지 않는다.
   - input contract, output contract, required capability, safety policy, guide를 포함한다.
   - Hermes, Claude Code, Codex, MCP client, local script가 같은 workflow package를 각자 실행할 수 있어야 한다.

### 3.4 구현 범위 원칙

Continuum은 MVP로 작게 끝내는 제품이 아니라, 아래 capability를 모두 구현해야 하는 장기 제품이다. 다만 구현은 위험도가 낮은 순서로 나누고, 각 phase는 다음 phase를 막지 않는 안정적인 기반을 남겨야 한다.

1. **CLI-first, MCP-ready, daemon-capable** — CLI를 먼저 만들되 MCP server와 daemon이 같은 service layer를 쓰도록 설계한다.
2. **Single-writer first, lease-ready** — 초기에는 단일 writer로 안전하게 시작하되 multi-agent claim/lease 모델을 같은 queue abstraction 안에 포함한다.
3. **Polling first, push-ready** — polling collector를 먼저 검증하되 push/webhook inbox와 trigger policy를 동일 item/segment 모델에 합류시킨다.
4. **Static routing first, dynamic routing-ready** — hardcoded/static routing으로 시작하되 routing rule schema와 audit view는 dynamic rule engine까지 견딜 수 있어야 한다.
5. **Immutable segment** — segment 내용 변경 시 새 segment를 만들고 기존 segment를 supersede한다.
6. **Default sensitivity at ingest** — 민감도는 ingest 시점에 source 기본값으로 부여한다.
7. **Derived output is not routing input by default** — output 재순환을 기본 차단한다.
8. **Unrouted is visible** — routing되지 않은 segment는 audit 대상이다.
9. **Proposal before side effect** — 외부 write/execute는 proposal/draft와 approval state를 거친다.

### 3.5 원칙 위배 체크리스트

새 기능/스키마/worker를 추가할 때마다 아래 질문에 답한다.

| 질문 | 위배 신호 |
|---|---|
| 이 기능이 어떤 사용자 가치를 높이는지 설명할 수 있는가? | 가치 없는 구현 취향 |
| 특정 agent 없이는 core가 동작하지 않는가? | agent 종속성 |
| CLI 또는 MCP 한쪽에만 business logic이 있는가? | surface 종속성 |
| source별 특수 정책이 core schema/worker로 들어오는가? | core 비대화 |
| output에서 원본 source/person/channel/run/context bundle을 추적할 수 있는가? | provenance/lineage 누락 |
| trust와 sensitivity를 섞어서 판단하고 있는가? | trust/privacy 혼동 |
| 처리 상태가 DB가 아니라 agent 기억에만 있는가? | implicit state |
| 근거 데이터가 update/delete 되는가? | immutable evidence 위반 |
| 실패/권한부족/unrouted/conflict가 사용자에게 보이지 않는가? | silent failure |
| 외부 side effect가 승인 없이 실행되는가? | human approval 위반 |
| 자동화 수준을 검증 없이 바로 execute로 올리는가? | progressive automation 위반 |
| 운영자가 CLI/파일/DB로 상태를 점검할 수 없는가? | inspectability 위반 |
| 같은 입력 재실행 시 중복/오염이 생기는가? | idempotency 위반 |
| 민감 정보가 기본 허용으로 흐르는가? | privacy 위반 |
| output이 실제로 채택/수정/폐기/실행됐는지 측정하지 않는가? | outcome metric 누락 |
| output 생성 입력이 명시적 context bundle 없이 agent 암묵 상태에만 남는가? | context packaging 누락 |
| workflow 정의가 특정 host/prompt/cron에만 갇혀 있는가? | portability 위반 |

---
