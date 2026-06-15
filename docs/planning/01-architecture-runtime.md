# Architecture, Sources, and Runtime

> Part of the Continuum planning docs. See [planning index](README.md).

## System Architecture and Storage

### 4. 전체 아키텍처

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

### 5. 저장 경로

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

---

## Source Sync and Ingest

### 7. Slack / append stream 처리

Slack은 가장 까다로운 케이스다.

#### 7.1 수집

Slack은 하나의 단순 append stream으로 보면 안 된다.

```text
channel timeline = append stream
thread replies = item-level mutable aggregate
```

각 channel이 stream이다.

```text
stream.key = slack:alpaon:#synapus
shape = append_entry
stream_cursor = latest_channel_ts
```

collector는 channel timeline을 watermark window와 함께 수집한다.

```text
fetch range = [latest_channel_ts - watermark_window, now]
```

이 단계에서 새 root message, 일반 message, thread root 후보를 찾는다.

#### 7.2 item 단위

각 메시지는 item이다.

```text
external_id = workspace_id:channel_id:message_ts
item_type = message
```

thread가 있으면 thread root도 item이 될 수 있다.

```text
external_id = workspace_id:channel_id:thread_ts
item_type = thread
```

#### 7.3 segment 단위

- 짧은 메시지: `message` segment 1개
- thread reply: reply별 `message` segment
- 긴 thread: 최신 reply 집합 기준 `thread_summary` segment
- unread/activity snapshot: artifact로 저장하되, 직접 workflow 처리 단위로 보지 않음

Thread summary는 aggregate segment다.

```text
thread_summary_version_1 = reply 1~5 기준
thread_summary_version_2 = reply 1~10 기준
```

thread가 자라면 기존 summary를 수정하지 않고 새 summary를 만들며, 기존 summary는 superseded 처리한다.

#### 7.4 conversation child sync 예시

Conversation은 stream cursor만으로는 충분하지 않다. Slack thread는 `conversation + children_grow`의 대표 예시다.

예:

```text
어제 수집: thread T reply 1~5
오늘 수집: thread T reply 1~10
```

처리 방식:

1. channel timeline 수집에서 thread root의 `reply_count` 또는 `latest_reply` 변화를 감지한다.
2. `item_sync_state(item_id=T, sync_kind=children_grow)`를 읽는다.
3. `reply_count_seen` 또는 `latest_reply_ts`가 증가했으면 Slack conversations.replies를 호출한다.
4. 기존 reply 1~5는 `external_id` unique constraint로 dedupe한다.
5. 새 reply 6~10만 item/segment로 추가한다.
6. thread 전체 의미가 바뀌었으므로 새 `thread_summary` segment를 만든다.
7. 기존 `thread_summary`는 `superseded_by_segment_id`로 새 summary에 연결한다.
8. 새 reply segments와 새 summary segment를 routing한다.
9. `item_sync_state`를 최신 reply 상태로 update한다.

```text
stream_cursors
  slack channel latest_channel_ts

item_sync_state
  thread T latest_reply_ts
  thread T reply_count_seen
```

즉 Slack은 두 단계 상태를 가진다.

```text
stream-level cursor: 새 channel message 발견
item-level sync state: 기존 thread 내부 증가분 발견
```

#### 7.5 수정/삭제

Slack 메시지는 수정/삭제될 수 있다.

수정/삭제 정책:

- 수정: 새 segment 생성 + 기존 segment supersede
- 삭제: item status를 `deleted`로 바꾸고 tombstone metadata를 남김
- 이미 생성된 report/diary/GBrain output은 당시 시점 스냅샷으로 유지
- 추가 답글로 thread 의미가 바뀌면 새 `thread_summary` segment 생성

#### 7.6 late arrival / watermark

append stream cursor는 단순 `latest_ts`만 믿지 않는다.

```text
cursor = latest_seen_ts
watermark_window = 최근 10~30분 재스캔
```

뒤늦게 나타난 메시지, retry, thread reply 누락을 줄이기 위해 collector는 watermark window 안의 최근 구간을 반복 스캔한다.

#### 7.7 snapshot 처리

`unread`, `activity`, `channels`는 직접 workflow 처리 단위가 아니라 snapshot artifact다.

단, report가 사용할 필요가 있으면 normalizer가 별도 `source_health` 또는 `summary` segment를 만든다.

---

### 8. Push와 polling

Continuum은 polling과 push를 모두 지원해야 한다. 구현 순서는 polling collector를 먼저 안정화하고, 이후 push/webhook을 같은 item/segment 모델에 붙이는 방식이다.

#### 8.1 Polling

예:

```bash
continuum collect plaud
continuum collect slack --stream slack:alpaon:#synapus
continuum workflow run morning_report
```

cron이 이 명령을 주기적으로 실행한다.

#### 8.2 Push

Push/webhook runtime은 선택적 확장이 아니라 Continuum의 필수 capability다. 다만 polling collector와 같은 item/segment 모델로 합류해야 하므로, polling 경로를 먼저 안정화한 뒤 같은 ledger에 붙인다.

외부 이벤트가 오면 `_inbox`에 먼저 기록하고, 즉시 workflow trigger를 평가한다.

```text
webhook event
  ↓
continuum ingest-event --source zapier --payload event.json
  ↓
item/segment 생성
  ↓
trigger policy 평가
  ↓
workflow enqueue
```

예:

- Plaud transcript generated Zapier event
- Slack event API
- Gmail push notification
- calendar event changed
- manual file dropped

#### 8.3 Trigger policy

Trigger policy도 필수 runtime capability다. 초기 구현은 static schedule과 static routing rule로 시작할 수 있지만, 최종적으로는 polling과 push trigger를 모두 같은 workflow contract에 표현해야 한다.

예:

```json
{
  "on_new_segment": {
    "segment_types": ["summary", "action_candidate"],
    "sources": ["plaud", "slack", "mail"],
    "run": "todo_planner"
  },
  "schedule": "0 8 * * *"
}
```

---

---

## Runtime, CLI, and MCP

### 9. Runtime 사용 모델

Continuum은 “CLI를 설치하고 skill 파일 하나를 등록하면 끝나는” 구조가 아니다. CLI, runtime DB, workflow package/skill, agent/MCP가 각각 다른 역할을 맡는다.

#### 9.0.1 역할 분리

| 구성요소 | 역할 | 필수 여부 |
|---|---|---|
| `continuum` CLI | runtime DB 초기화, source 수집, workflow queue 조회/처리, output/lineage/feedback 기록 | 필수 |
| runtime DB/files | `runtime/continuum.db`, artifacts, outputs, logs. 실제 상태와 근거의 SSOT | 필수 |
| workflow package | workflow의 input/output contract, required capabilities, safety policy, guide | workflow 실행 시 필수 |
| Hermes skill | Hermes가 특정 workflow package를 어떻게 사용할지 알려주는 host adapter/사용법 문서 | Hermes 연동 시 필요 |
| MCP server | Claude Desktop, Hermes MCP client, 다른 agent가 Continuum을 표준 tool surface로 쓰는 통합 채널 | 필수 capability |

즉 skill은 “agent에게 사용법을 가르치는 파일”이지, Continuum runtime 자체가 아니다. 실제 상태 변화는 CLI/MCP가 같은 core service layer를 통해 DB에 기록해야 한다.

#### 9.0.2 실제 사용 흐름

```text
1. 설치
   uv tool install continuum
   # 또는 OS/패키징 방식에 따라 pipx/brew/pkg installer 사용

2. 온보딩
   continuum setup
   # runtime path, DB 초기화, connector credential, 기본 workflow, agent integration을 안내

3. 상태 점검
   continuum doctor

4. source 등록/수집/정규화
   continuum streams add slack:alpaon:#synapus --shape append_entry --connector slack
   continuum streams add plaud:account:default --shape recording --connector plaud
   continuum collect slack --workspace alpaon
   continuum collect plaud
   continuum normalize --pending

5. routing materialize
   continuum route --workflow morning_report
   continuum workflows pending morning_report

6. agent/workflow 실행
   Hermes skill 또는 workflow package가 pending segment를 읽고 context bundle을 만든다.
   agent는 report/draft/proposal을 생성한다.

7. 결과 기록
   continuum bundles create ...
   continuum outputs create ...
   continuum lineage add ...
   continuum workflows mark morning_report <segment_id> processed

8. feedback 기록
   continuum outputs feedback <output_id> accepted|edited|rejected|executed
```

개발자만 repo를 clone한다.

```bash
git clone https://github.com/kimjisub/continuum
cd continuum
uv sync
uv run continuum
```

#### 9.0.3 Hermes skill은 어디에 쓰이나

Hermes skill은 다음을 담는다.

```text
name: continuum-morning-report
what it does: Continuum pending segments로 morning report 생성
commands it may call:
  - continuum workflows pending morning_report
  - continuum bundles create ...
  - continuum outputs create ...
  - continuum lineage add ...
  - continuum outputs feedback ...
safety:
  - external side effect는 proposal/draft까지만
  - approval 전 calendar/reminder/mail/slack write 금지
```

Hermes runtime에서는 이 skill을 로드한 뒤 CLI를 호출해 Continuum DB를 읽고 쓴다. 따라서 “skill 등록”은 사용 가능 조건 중 하나지만, 충분조건은 아니다.

필요한 것:

1. `continuum` CLI가 설치되어 PATH에서 실행 가능해야 한다.
2. runtime DB가 초기화되어 있어야 한다.
3. source connector 설정과 credentials가 있어야 한다.
4. workflow가 DB에 등록되어 있어야 한다.
5. Hermes skill 또는 MCP tool이 해당 workflow contract를 알고 있어야 한다.

#### 9.0.4 MCP가 붙으면 달라지는 점

MCP가 생기면 Hermes skill이 직접 CLI 명령을 조립하는 대신, tool call로 Continuum을 쓴다.

```text
Hermes/Claude/Codex
  → MCP tool: continuum_list_pending
  → MCP tool: continuum_create_context_bundle
  → MCP tool: continuum_submit_output
  → MCP tool: continuum_record_feedback
  → Continuum core service
  → runtime DB/files
```

CLI와 MCP는 서로 다른 구현이 아니라 같은 core service layer의 두 surface여야 한다.

#### 9.0.5 Daemon / background process 모델

기본 runtime은 **always-on daemon을 요구하지 않는다.** Continuum의 기본 단위는 짧게 실행되고 종료되는 CLI command다.

```text
cron / Hermes cron / launchd / shell
  → continuum collect ...
  → continuum route ...
  → continuum workflows pending ...
  → continuum outputs create ...
  → exit
```

이 방식을 기본값으로 두는 이유:

- local-first와 inspectability가 좋다.
- 죽어 있는 daemon 때문에 수집이 멈추는 failure mode를 줄인다.
- 사용자는 `continuum doctor`, DB, log 파일로 상태를 직접 확인할 수 있다.
- 초기 single-writer 운영과 잘 맞는다.

다만 장기적으로는 두 종류의 long-running process가 있을 수 있다.

| Process | 명령 | 역할 | 필수 여부 |
|---|---|---|---|
| MCP server | `continuum mcp serve` | 외부 agent/host에 MCP tools 노출 | MCP 연동 시 필요 |
| Continuum daemon | `continuum daemon` | local scheduler, file watcher, queue worker, health monitor | 필수 capability, 기본 설치에서는 off |

따라서 설치 후 기본 UX는 daemon을 켜는 것이 아니라:

```bash
continuum setup
continuum doctor
## 필요하면 Hermes cron/OS cron에 collect/route/workflow command 등록
```

MCP 연동을 선택한 경우에만 host가 `continuum mcp serve`를 background process로 관리한다. 예를 들어 Hermes MCP 설정, Claude Desktop MCP 설정, launchd/systemd user service가 이 프로세스를 띄울 수 있다.

#### 9.0.6 현재 구현 상태

현재 repo의 CLI는 bootstrap 단계다. `pyproject.toml`에 `continuum = "continuum.cli:main"` entry point는 있지만, `src/continuum/cli.py`는 아직 planning/bootstrap 메시지만 출력한다.

따라서 현재 당장 가능한 것은:

```bash
cd ~/Github/kimjisub/continuum
uv sync
uv run continuum
```

현재 당장 불가능한 것은:

```bash
continuum init
continuum collect ...
continuum workflows pending ...
continuum outputs create ...
```

이 명령들은 설계상 필요한 runtime surface이고, 다음 구현 단계에서 만들어야 한다.

---

### 9. CLI 인터페이스

CLI 이름 제안: `continuum`

#### 9.1 초기화

```bash
continuum init
continuum doctor
continuum stats
```

#### 9.2 connector 관리

```bash
continuum streams list
continuum streams add slack:alpaon:#synapus --shape append_entry --connector slack
continuum streams show slack:alpaon:#synapus
```

#### 9.3 수집

```bash
continuum collect plaud
continuum collect slack --workspace alpaon
continuum collect mail --account google
continuum collect calendar
```

#### 9.4 item/segment 조회

```bash
continuum items list --source plaud --since 2026-06-14
continuum items show <item_id>
continuum segments list --item <item_id>
continuum segments pending --workflow daily_report
```

#### 9.5 workflow 처리

```bash
continuum workflows list
continuum workflows pending daily_report
continuum workflows run daily_report --date 2026-06-15
continuum workflows mark daily_report <segment_id> processed
continuum workflows retry daily_report --failed
```

초기 운영에서는 위 명령을 single-writer process/operator만 실행한다. 외부 agent는 기본적으로 read-only + output/draft 제출로 제한하고, claim/lease가 활성화되면 여러 worker가 안전하게 처리할 수 있다.

#### 9.6 lineage

```bash
continuum lineage output report:daily:2026-06-15
continuum lineage item <item_id>
```

#### 9.7 drafts

```bash
continuum drafts list --status draft
continuum drafts show <draft_id>
continuum drafts create --type reply --format md --based-on <segment_id> --path draft.md
continuum drafts approve <draft_id>
continuum drafts reject <draft_id> --reason not_needed
continuum drafts supersede <draft_id> --path revised.md
continuum drafts execute <draft_id>   # code draft 등 명시 승인 후 실행
```

초안 실행은 기본적으로 위험한 side effect이므로 `approve`와 별도 `execute`를 분리한다.

#### 9.8 MCP interface

MCP는 Continuum을 agent/host가 표준 protocol로 쓰기 위한 1급 integration surface다.

CLI를 먼저 구현하되, 아래 기능은 MCP tool로 그대로 노출 가능한 boundary를 유지한다.

| MCP tool 후보 | 대응 CLI | 용도 |
|---|---|---|
| `continuum_search_segments` | `continuum segments ...` | workflow/agent가 context 검색 |
| `continuum_get_context_bundle` | `continuum bundles show` | curated context bundle 조회 |
| `continuum_create_context_bundle` | `continuum bundles create` | 목적별 context packaging |
| `continuum_list_pending` | `continuum workflows pending` | workflow queue 조회 |
| `continuum_submit_output` | `continuum outputs create` | agent/worker output 제출 |
| `continuum_submit_draft` | `continuum drafts create` | draft 제출 |
| `continuum_record_feedback` | `continuum outputs feedback` | outcome feedback 기록 |
| `continuum_get_lineage` | `continuum lineage ...` | 근거 추적 |

원칙:

- MCP tool은 CLI subprocess wrapper가 아니라 core service boundary를 공유한다.
- CLI와 MCP는 같은 Python service/domain layer를 호출한다.
- MCP는 외부 host가 Continuum을 읽고 쓰는 표준 surface지만, local debugging과 cron 운영을 위해 CLI도 동등하게 유지한다.

---
