# Blindtest — API & WebSocket Contracts

**Source of truth**: backend Pydantic schemas in `backend/src/api/schemas/`.  
**TypeScript types**: `packages/contracts/index.ts` mirrors these contracts.  
**Tests**: `backend/tests/api/test_contracts.py` freezes the shapes with assertions.

---

## HTTP API

### POST /rooms

**Request**
```json
{ "host_nickname": "Alice" }
```

**Response** `201`
```json
{
  "room_id": "uuid",
  "code": "ABC123",
  "host_id": "uuid"
}
```

**Errors**: `422` (missing/empty nickname)

---

### POST /rooms/{code}/join

**Request**
```json
{ "nickname": "Bob" }
```

**Response** `201`
```json
{
  "room_id": "uuid",
  "participant_id": "uuid"
}
```

**Errors**: `404` (room not found), `409` (room not joinable, nickname taken), `422`

---

### POST /rooms/{room_id}/rounds

**Request**
```json
{ "theme": "Pop 90s" }
```

**Response** `201`
```json
{
  "round_id": "uuid",
  "room_id": "uuid",
  "song_count": 10,
  "theme": "Pop 90s"
}
```

**Errors**: `404` (room not found), `409` (room not waiting)

Also triggers WebSocket broadcasts: `round.started` then `song.started` for song 0.

---

### POST /rounds/{round_id}/songs/{song_index}/start

**Request**: empty body

**Response** `200`
```json
{
  "song_id": "uuid",
  "round_id": "uuid",
  "room_id": "uuid",
  "song_index": 2,
  "started_at": "2026-01-01T12:00:00+00:00",
  "ends_at": "2026-01-01T12:00:30+00:00",
  "preview_url": "https://cdn.deezer.com/preview.mp3"
}
```

`preview_url` is `null` when no Deezer preview is available.

Also triggers: `song.started` WebSocket event; auto-lock background task sends `song.locked` after timer.

---

### POST /songs/{song_id}/answers

**Request**
```json
{ "participant_id": "uuid", "text": "Daft Punk" }
```

**Response** `201`
```json
{
  "answer_id": "uuid",
  "submitted_at": "2026-01-01T12:00:05+00:00",
  "validation_status": "found",
  "title_found": false,
  "artist_found": true
}
```

`validation_status` ∈ `"not_found" | "found" | "doubtful"`

**Errors**: `404` (song not found), `409` (song not accepting answers)

---

### GET /songs/{song_id}/summary?host_id={uuid}

**Response** `200`
```json
{
  "song_id": "uuid",
  "title": "Get Lucky",
  "artist": "Daft Punk",
  "total_answers": 3,
  "doubtful_count": 1,
  "answers": [
    {
      "answer_id": "uuid",
      "participant_id": "uuid",
      "nickname": "Alice",
      "text": "get lucky",
      "validation_status": "found",
      "title_found": true,
      "artist_found": true
    }
  ]
}
```

**Errors**: `403` (not host), `404` (song not found), `409` (song not locked)

---

### PATCH /songs/{song_id}/answers/{answer_id}

**Request**
```json
{ "host_id": "uuid", "title_accepted": true, "artist_accepted": false }
```

**Response** `200`
```json
{
  "answer_id": "uuid",
  "title_found": true,
  "artist_found": false,
  "validation_status": "doubtful",
  "score": 1
}
```

**Errors**: `403` (not host), `404` (song/answer not found), `409` (song not correctable)

---

### POST /songs/{song_id}/reveal

**Request**
```json
{ "host_id": "uuid" }
```

**Response** `200`
```json
{
  "song_id": "uuid",
  "room_id": "uuid",
  "title": "One More Time",
  "artist": "Daft Punk",
  "player_results": [
    {
      "participant_id": "uuid",
      "nickname": "Alice",
      "answer": "one more time",
      "title_found": true,
      "artist_found": false,
      "score": 117
    }
  ],
  "mini_leaderboard": [
    {
      "rank": 1,
      "participant_id": "uuid",
      "nickname": "Alice",
      "total_points": 234
    }
  ],
  "round_finished": false,
  "round_leaderboard": []
}
```

When `round_finished: true`, `round_leaderboard` contains:
```json
[{ "rank": 1, "participant_id": "uuid", "nickname": "Alice", "round_points": 200 }]
```

Also triggers: `song.revealed` WebSocket event; `round.finished` event when `round_finished: true`.

**Errors**: `403` (not host), `404` (song not found), `409` (song not revealable)

---

## WebSocket

**URL**: `ws://<host>/ws/rooms/{room_id}`

All events share the envelope `{ "event": "<name>", "data": { ... } }`.

---

### room.state

Sent immediately on connection.

```json
{
  "event": "room.state",
  "data": {
    "room_id": "uuid",
    "participants": [
      { "participant_id": "uuid", "nickname": "Alice", "is_host": true }
    ]
  }
}
```

---

### participant.joined

Broadcast when a player joins via `POST /rooms/{code}/join`.

```json
{
  "event": "participant.joined",
  "data": {
    "participant_id": "uuid",
    "nickname": "Bob",
    "is_host": false
  }
}
```

---

### round.started

Broadcast when a round begins (`POST /rooms/{room_id}/rounds` or `/restart`).

```json
{
  "event": "round.started",
  "data": {
    "round_id": "uuid",
    "theme": "Pop 90s",
    "song_count": 10
  }
}
```

---

### song.started

Broadcast when a song timer begins.

```json
{
  "event": "song.started",
  "data": {
    "song_id": "uuid",
    "song_index": 0,
    "round_id": "uuid",
    "started_at": "2026-01-01T12:00:00+00:00",
    "ends_at": "2026-01-01T12:00:30+00:00",
    "preview_url": "https://cdn.deezer.com/preview.mp3"
  }
}
```

`preview_url` is `null` when unavailable.

---

### song.locked

Broadcast automatically when the timer expires (30 s after `song.started`).

```json
{
  "event": "song.locked",
  "data": {
    "song_id": "uuid",
    "round_id": "uuid"
  }
}
```

---

### song.revealed

Broadcast when the host calls `POST /songs/{song_id}/reveal`.

```json
{
  "event": "song.revealed",
  "data": {
    "song_id": "uuid",
    "title": "One More Time",
    "artist": "Daft Punk",
    "player_results": [
      {
        "participant_id": "uuid",
        "nickname": "Alice",
        "answer": "one more time",
        "title_found": true,
        "artist_found": false,
        "score": 117
      }
    ],
    "mini_leaderboard": [
      {
        "rank": 1,
        "participant_id": "uuid",
        "nickname": "Alice",
        "total_points": 234
      }
    ]
  }
}
```

---

### round.finished

Broadcast on the last song reveal of a round (only when `round_finished: true`).

```json
{
  "event": "round.finished",
  "data": {
    "room_id": "uuid",
    "round_leaderboard": [
      {
        "rank": 1,
        "participant_id": "uuid",
        "nickname": "Alice",
        "round_points": 200
      }
    ]
  }
}
```

---

## Event flow (happy path)

```
Client connects  →  room.state
Host starts round  →  round.started, song.started
Timer expires  →  song.locked
Host reveals  →  song.revealed  [+round.finished on last song]
Host starts next song  →  song.started
...
```
