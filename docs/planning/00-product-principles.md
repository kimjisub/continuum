# Product Principles

> Part of the Continuum planning docs. See [planning index](README.md).

## Overview, Values, Philosophy, Principles

## Continuum 기획서

> 작업명: **Continuum**
> 한 줄 정의: **Hermes와 다른 agent들이 공유하는 개인 맥락 ledger. Source item/segment, workflow 처리 상태, output lineage를 구조적으로 기록한다.**

---

### 1. 왜 Continuum인가

Continuum은 사용자의 맥락이 끊기지 않고 흐르는 하나의 연속체라는 의미다.

우리가 원하는 가치는:

> Hermes가 실행하고, Continuum이 상태와 근거를 남긴다. 사용자의 맥락이 특정 agent의 기억이나 cron prompt 안에 갇히지 않고, workflow 처리 상태와 output lineage까지 추적되는 SSOT.

이 이름이 적합한 이유:

- 끊기지 않는 맥락의 흐름을 표현한다.
- 특정 source나 workflow에 묶이지 않는 추상화 계층을 뜻한다.
- Hermes뿐 아니라 다른 agent, local script, MCP server도 붙을 수 있는 중립적 core를 지향한다.
- 단순 저장소가 아니라 source/workflow/output 사이의 ledger를 나타낸다.

#### 1.1 역할 분리

Continuum은 Hermes를 대체하는 새 agent platform이 아니다. Hermes가 이미 잘하는 실행/대화/스케줄링/도구 호출은 Hermes에 맡기고, Continuum은 Hermes가 일관되게 참조할 수 있는 상태와 근거를 기록한다.

| 역할 | 담당 | 하지 않는 일 |
|---|---|---|
| **Hermes Agent** | 대화 UI, Telegram/Discord gateway, cron 실행, tool call, LLM reasoning, 사용자 승인 요청, 실제 작업 수행 | source별 처리 상태와 lineage의 장기 SSOT가 되지 않는다 |
| **Continuum** | source item/segment ledger, workflow queue state, context bundle, output/draft/proposal lineage, feedback/metric, reconcile 기록 | 자체 대화 UI나 범용 agent runtime이 되지 않는다 |
| **외부 시스템** | Slack, Mail, Calendar, Reminders, GBrain 등 실제 source와 write target | Continuum의 내부 처리 상태를 알지 못한다 |
| **MCP/CLI** | Hermes와 다른 host가 Continuum ledger를 읽고 쓰는 surface | business logic을 독점하지 않는다. 같은 service layer를 호출한다 |

따라서 기본 구조는 다음과 같다.

```text
Hermes = 실행자 / 사용자 접점 / 스케줄러 / agent orchestration
Continuum = 맥락 ledger / workflow state / lineage / reconcile 기록
외부 시스템 = 실제 데이터 source와 side-effect 대상
```

Continuum의 성공 기준은 “Hermes 없이 모든 것을 한다”가 아니라, Hermes가 처리한 일이 **어떤 맥락에서 시작됐고, 어떤 상태를 거쳐, 어떤 output/side effect로 이어졌는지**를 재현 가능하게 남기는 것이다.

---

### 2. 가치 — 왜 이 제품이 필요한가

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

### 2.5 철학 — 무엇을 믿고 어떤 방향을 선택하는가

여기서 **철학**은 개별 규칙 목록이 아니라, Continuum이 반복해서 선택해야 하는 trade-off의 방향이다.
철학은 “왜 그런 설계를 택하는가”를 설명하고, 원칙은 그 철학을 구현할 때 지킬 판단 기준이다.

Continuum의 철학은 다음과 같다.

#### 2.5.1 맥락은 agent의 기억이 아니라 사용자의 자산이다

Continuum은 특정 agent, 특정 앱, 특정 모델의 memory가 아니다.
사용자의 맥락은 사용자 소유의 중립 core에 남아야 하며, Hermes, Claude Code, Codex, Gemini, local script, MCP server, custom agent는 모두 그 core를 읽고 쓰는 consumer/producer일 뿐이다.

이 철학이 의미하는 것:

- agent가 바뀌어도 맥락, 처리 상태, lineage, trust/sensitivity 평가는 유지된다.
- core는 특정 host의 prompt나 memory 기능에 종속되지 않는다.
- CLI와 MCP는 surface일 뿐이고, 실제 판단과 상태는 공통 domain/service layer에 남는다.

#### 2.5.2 기록보다 해석이 먼저가 아니라, 근거 있는 해석이 먼저다

Continuum은 “좋은 요약”보다 “근거를 설명할 수 있는 요약”을 우선한다.
모든 output은 어떤 source에서 왔고, 어떤 actor와 관련 있고, 어떤 segment/context bundle을 근거로 삼았는지 설명 가능해야 한다.

이 철학이 의미하는 것:

- provenance, lineage, trust, sensitivity는 부가기능이 아니라 core다.
- 모순된 정보는 덮어쓰지 않고 conflict로 남긴다.
- 최신 정보가 항상 정답은 아니며, 더 강한 근거가 우선될 수 있다.

#### 2.5.3 자동화는 사람을 대체하기보다 승인 가능한 선택지를 만든다

Continuum의 기본 자동화 단계는 `observe → propose/draft → approve → execute`다.
외부 시스템에 영향을 주는 write/execute는 처음부터 완전 자동화하지 않는다.

이 철학이 의미하는 것:

- todo 생성, calendar write, Slack/메일 전송, GBrain 저장, 코드 실행은 기본적으로 proposal/draft를 먼저 만든다.
- 충분히 검증된 낮은 위험 작업만 trusted rule로 승격한다.
- 위험도가 높을수록 더 명시적인 승인과 더 강한 lineage가 필요하다.

#### 2.5.4 core는 얇고 안정적이어야 하며, 풍부함은 edge에서 나온다

Continuum core는 모든 제품 정책을 품은 거대한 앱이 아니다.
core는 맥락을 수집·정규화·라우팅·추적하는 substrate이고, 실제 사용 정책은 source adapter와 workflow/application edge에서 발전한다.

이 철학이 의미하는 것:

- Slack/Plaud/Mail/Calendar별 특수 정책은 adapter/guide로 밀어낸다.
- daily report, diary, todo planner, gbrain fanout의 제품 판단은 workflow edge가 담당한다.
- core가 비대해지면 agent-neutral, inspectable, portable한 성격이 깨진다.

#### 2.5.5 로컬에서 설명 가능해야 확장도 가능하다

Continuum은 처음부터 분산 orchestration이나 외부 queue를 전제로 하지 않는다.
먼저 local-first, inspectable, recoverable하게 만들고, 그 위에 sync/cloud/multi-device를 붙일 수 있는 구조를 유지한다.

이 철학이 의미하는 것:

- 사람이 SQLite, filesystem, CLI로 상태를 점검하고 복구할 수 있어야 한다.
- 재처리와 디버깅이 가능하도록 run/input/output/lineage를 남긴다.
- protocol surface는 MCP를 1급 지원하되, 운영 가능한 CLI를 버리지 않는다.

---

### 3. 원칙 — 설계와 구현에서 지킬 판단 기준

여기서 **원칙**은 철학을 실제 설계로 옮길 때 적용하는 구체적 판단 기준이다.
원칙은 “좋은 말”이 아니라 스키마, worker, CLI/MCP, workflow 구현에서 위반 여부를 판정할 수 있어야 한다.

#### 3.1 데이터 모델링 원칙

00 문서에서는 data shape, sync behavior, table 설계의 세부 목록을 다루지 않는다. 세부 분류와 스키마는 [Data Model](02-data-model.md)에 둔다. 여기에는 설계 판단을 좌우하는 원칙만 남긴다.

##### 3.1.1 Source 이름보다 data shape을 먼저 본다

“Slack 전용”, “Plaud 전용”, “Reminder 전용” 모델을 먼저 만들지 않는다. 외부 객체가 어떤 형태의 데이터인지, 어떻게 동기화되는지, workflow가 어떤 단위로 읽어야 하는지를 먼저 본다.

핵심 질문:

- 이 객체는 stream entry인가, conversation인가, task인가, document인가, snapshot인가?
- 새로 append되는가, child가 자라는가, 같은 record가 수정되는가, 버전이 생기는가?
- workflow가 읽어야 하는 최소 단위는 item인가, artifact인가, segment인가?

##### 3.1.2 읽기 모델과 쓰기 모델을 분리한다

같은 외부 시스템이 **source**이면서 동시에 **write target**일 수 있다. Todo list, Calendar, GBrain, Slack, Mail이 모두 그렇다.

원칙:

- 외부 시스템에서 이미 존재하는 객체를 읽어온 것은 `source item/segment`다.
- Continuum이 외부 시스템에 쓰려고 만든 것은 먼저 `proposal/draft/output`이다.
- 실제 write/execute는 승인 가능한 side effect로 다루고, 실행 결과는 다시 source 수집을 통해 `item/segment`로 reconcile한다.
- 즉 “내가 만들 todo”와 “실제로 Reminders에 존재하는 todo”를 같은 것으로 착각하지 않는다.

예:

```text
Reminder existing task
  → source item/segment

Todo proposal generated by Continuum
  → output/draft/proposal
  → user approval
  → external write to Reminders
  → next collect reconciles created reminder as source item
  → lineage links proposal/output to created source item
```

이렇게 해야 output 재순환, 중복 todo 생성, 외부 시스템과 Continuum DB의 상태 불일치를 줄일 수 있다.

##### 3.1.3 원본/근거는 immutable, 상태는 mutable로 분리한다

- artifact/segment/output/lineage는 덮어쓰지 않는다.
- cursor/workflow state/draft status처럼 현재 상태를 나타내는 값만 update한다.
- 수정/재생성은 새 row와 supersede/version으로 표현한다.

##### 3.1.4 출처, 신뢰도, 민감도는 처음부터 함께 저장한다

- provenance는 나중에 붙이는 설명이 아니라 데이터의 일부다.
- sensitivity는 LLM 판단 이전 ingest 시점에 보수적으로 부여한다.
- trust와 sensitivity는 분리한다. 믿을 만한 정보라도 민감할 수 있고, 공개 정보라도 신뢰도가 낮을 수 있다.

##### 3.1.5 derived output은 기본적으로 다시 routing input이 아니다

- report/diary/todo proposal이 다시 입력으로 순환하면 맥락 오염과 중복 판단이 생긴다.
- output을 재입력으로 쓰려면 명시적 workflow rule과 lineage가 필요하다.
- 외부 write 결과는 output 자체가 아니라, 다음 수집에서 확인된 source item으로 다시 들어와야 한다.

#### 3.2 처리/운영 원칙

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

#### 3.3 인터페이스/확장 원칙

1. **실행은 agent/edge가, 상태는 Continuum이 맡는다**
   - Hermes는 reasoning, tool call, 사용자 대화, 승인 요청, 실제 실행을 담당한다.
   - Continuum은 source item/segment, workflow state, context bundle, output lineage, feedback을 기록한다.
   - Continuum이 범용 agent runtime이나 대화 UI가 되면 역할 경계가 무너진다.

2. **Core logic은 CLI/MCP 밖에 둔다**
   - CLI와 MCP는 같은 service/domain layer를 호출한다.
   - 어느 한 surface에만 business logic이 있으면 agent-neutral이 깨진다.

3. **MCP는 agent 통합의 1급 surface다**
   - 외부 agent가 Continuum을 subprocess hack으로만 쓰게 만들지 않는다.
   - MCP tool은 초기에는 read-only + output/draft/context bundle 제출 중심으로 시작한다.
   - write/execute성 tool은 approval state를 요구한다.

4. **Workflow는 portable package로 정의한다**
   - workflow 정의를 특정 host의 prompt나 cron job에 가두지 않는다.
   - input contract, output contract, required capability, safety policy, guide를 포함한다.
   - Hermes, Claude Code, Codex, MCP client, local script가 같은 workflow package를 각자 실행할 수 있어야 한다.

#### 3.4 구현 범위 원칙

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

#### 3.5 원칙 위배 체크리스트

새 기능/스키마/worker를 추가할 때마다 아래 질문에 답한다.

| 질문 | 위배 신호 |
|---|---|
| 이 기능이 어떤 사용자 가치를 높이는지 설명할 수 있는가? | 가치 없는 구현 취향 |
| 특정 agent 없이는 core가 동작하지 않는가? | agent 종속성 |
| Continuum이 대화 UI/범용 agent runtime/LLM 실행자가 되려 하는가? | Hermes와 역할 중복 |
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
