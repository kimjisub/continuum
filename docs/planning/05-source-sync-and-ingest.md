# Source Sync and Ingest

> Part of the Continuum planning docs. See [planning index](README.md).

## 7. Slack / append stream 처리

Slack은 가장 까다로운 케이스다.

### 7.1 수집

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

### 7.2 item 단위

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

### 7.3 segment 단위

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

### 7.4 conversation child sync 예시

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

### 7.5 수정/삭제

Slack 메시지는 수정/삭제될 수 있다.

수정/삭제 정책:

- 수정: 새 segment 생성 + 기존 segment supersede
- 삭제: item status를 `deleted`로 바꾸고 tombstone metadata를 남김
- 이미 생성된 report/diary/GBrain output은 당시 시점 스냅샷으로 유지
- 추가 답글로 thread 의미가 바뀌면 새 `thread_summary` segment 생성

### 7.6 late arrival / watermark

append stream cursor는 단순 `latest_ts`만 믿지 않는다.

```text
cursor = latest_seen_ts
watermark_window = 최근 10~30분 재스캔
```

뒤늦게 나타난 메시지, retry, thread reply 누락을 줄이기 위해 collector는 watermark window 안의 최근 구간을 반복 스캔한다.

### 7.7 snapshot 처리

`unread`, `activity`, `channels`는 직접 workflow 처리 단위가 아니라 snapshot artifact다.

단, report가 사용할 필요가 있으면 normalizer가 별도 `source_health` 또는 `summary` segment를 만든다.

---

## 8. Push와 polling

Continuum은 polling과 push를 모두 지원해야 한다. 구현 순서는 polling collector를 먼저 안정화하고, 이후 push/webhook을 같은 item/segment 모델에 붙이는 방식이다.

### 8.1 Polling

예:

```bash
continuum collect plaud
continuum collect slack --stream slack:alpaon:#synapus
continuum workflow run morning_report
```

cron이 이 명령을 주기적으로 실행한다.

### 8.2 Push

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

### 8.3 Trigger policy

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
