# Notification System Design

---

## Stage 1

### REST API Design — Campus Notification Platform

#### Core Actions

The notification platform supports:
- Creating a notification (triggered by HR/admin)
- Fetching notifications for a student
- Marking one or all notifications as read
- Deleting a notification
- Real-time push via WebSocket subscription

---

#### Endpoints

##### `POST /api/notifications`
Create a new notification (admin/HR only).

**Request Body**
```json
{
  "student_ids": ["string"],
  "type": "Placement | Result | Event",
  "message": "string",
  "metadata": {
    "company": "string",
    "exam_name": "string",
    "event_name": "string"
  }
}
```

**Response 201**
```json
{
  "notification_id": "uuid",
  "type": "Placement",
  "message": "TCS hiring drive",
  "created_at": "2026-04-22T17:51:30Z",
  "recipient_count": 500
}
```

##### `GET /api/notifications`
Fetch notifications for the authenticated student.

**Query Params**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | — | Filter by type |
| `is_read` | bool | — | Filter by read status |
| `page` | int | 1 | Pagination |
| `limit` | int | 20 | Page size |

**Response 200**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "Placement",
      "message": "TCS hiring drive",
      "is_read": false,
      "created_at": "2026-04-22T17:51:30Z"
    }
  ],
  "total": 120,
  "page": 1,
  "limit": 20
}
```

##### `PATCH /api/notifications/:id/read`
Mark a single notification as read.

**Response 200**
```json
{ "id": "uuid", "is_read": true }
```

##### `PATCH /api/notifications/read-all`
Mark all as read.

**Response 200**
```json
{ "updated_count": 45 }
```

##### `DELETE /api/notifications/:id`
Delete a notification.

**Response 204** — No content.

##### `GET /api/notifications/unread-count`
Badge counter endpoint.

**Response 200**
```json
{ "unread_count": 7 }
```

#### Real-Time Notification Mechanism

**Approach: WebSocket with Redis Pub/Sub**

- Client opens WebSocket on login: `ws://host/ws/notifications?token=<jwt>`
- Server authenticates JWT, registers socket in memory map keyed by `student_id`
- On new notification → server pushes directly to connected sockets
- Offline students → notification persisted in DB, delivered on next login
- Horizontal scaling → Redis Pub/Sub channel `notifications:{student_id}`

**Push Payload**
```json
{
  "event": "new_notification",
  "data": {
    "id": "uuid",
    "type": "Placement",
    "message": "TCS hiring drive",
    "created_at": "2026-04-22T17:51:30Z"
  }
}
```

---

## Stage 2

### Persistent Storage

#### DB Choice: PostgreSQL

- Structured relational data with clear FK relationships
- JSONB for flexible metadata
- Native partial indexes critical for `isRead = false` pattern
- Mature tooling for replicas, partitioning, connection pooling

#### Schema

```sql
CREATE TYPE notification_type AS ENUM ('Placement', 'Result', 'Event');

CREATE TABLE students (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(255) NOT NULL,
    email      VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notifications (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type       notification_type NOT NULL,
    message    TEXT NOT NULL,
    metadata   JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE student_notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (student_id, notification_id)
);

CREATE INDEX idx_sn_student_unread
    ON student_notifications (student_id, created_at DESC)
    WHERE is_read = FALSE;
```

#### Scaling Solutions

| Problem | Solution |
|---------|----------|
| Billions of rows | Table partitioning by `created_at` monthly |
| Slow reads on page load | Redis cache per student |
| 50k student broadcast | Async message queue fan-out |
| Read replica lag | Route reads to replica, writes to primary |

#### SQL Queries

```sql
-- Fetch unread for student
SELECT n.id, n.type, n.message, n.created_at
FROM student_notifications sn
JOIN notifications n ON n.id = sn.notification_id
WHERE sn.student_id = 1042 AND sn.is_read = FALSE
ORDER BY n.created_at DESC;

-- Mark all read
UPDATE student_notifications
SET is_read = TRUE, read_at = NOW()
WHERE student_id = 1042 AND is_read = FALSE;
```
---

## Stage 3

### Query Analysis and Optimization

#### Original Query
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

#### Is it accurate?
No — read status lives in `student_notifications`, not `notifications`. Must JOIN both tables.

#### Why is it slow?
1. No index on `(studentID, isRead, createdAt)` — full sequential scan
2. `SELECT *` — fetches large JSONB metadata unnecessarily
3. No `LIMIT` — unbounded result set
4. Low-selectivity filter at scale

#### Computation Cost
Without index: O(n) sequential scan, hundreds of MB at 5M rows.
With partial index: O(log n + k) where k = result count.

#### Is "index every column" good advice?
No — harmful because:
- Every write must update all indexes
- Consumes disk and memory
- Query planner may pick wrong index

**Correct fix:**
```sql
CREATE INDEX idx_sn_student_unread
ON student_notifications (student_id, created_at DESC)
WHERE is_read = FALSE;
```

#### Placement notifications last 7 days
```sql
SELECT DISTINCT s.id, s.name, s.email
FROM students s
JOIN student_notifications sn ON sn.student_id = s.id
JOIN notifications n ON n.id = sn.notification_id
WHERE n.type = 'Placement'
  AND n.created_at >= NOW() - INTERVAL '7 days';
```

---

## Stage 4

### Performance Under Load

#### Problem
DB overwhelmed by notifications fetched on every page load for 50k students.

#### Strategy 1 — Redis Cache (Recommended)
- Cache hit → return immediately
- Cache miss → query DB → populate cache
- On new notification → INCR + ZADD
- On read → DECR

✅ Sub-millisecond response
✅ Near-zero DB load
❌ Extra Redis infrastructure

#### Strategy 2 — ETags
Return `ETag` header → client sends `If-None-Match` → `304 Not Modified` if unchanged.

✅ Reduces bandwidth
❌ DB still queried to compute ETag

#### Strategy 3 — Cursor Pagination
Enforce `LIMIT 20`, never load all at once.

✅ Bounds query cost
❌ Doesn't reduce hit frequency

**Recommended: Strategy 1 + Strategy 3 + Strategy 2**

---

## Stage 5

### Bulk Notification Redesign

#### Shortcomings of Original

1. Synchronous loop over 50k — guaranteed timeout
2. No atomicity — fails at student 200, rest never notified
3. No retry — failures silently dropped
4. Coupled operations — email failure blocks DB insert

#### Should DB save and email happen together?
No. DB insert is fast and local. Email is slow and unreliable.
Rule: **persist first, dispatch externally after.**

#### Redesigned — Message Queue

#### Revised Pseudocode
```python
async def notify_all(student_ids, message, type):
    notification_id = await db.insert_notification(type=type, message=message)
    await queue.enqueue("fan_out", {
        "notification_id": notification_id,
        "student_ids": student_ids,
        "message": message
    })
    return { "status": "queued", "notification_id": notification_id }

async def fan_out(job):
    for batch in chunks(job["student_ids"], 500):
        await db.bulk_insert(job["notification_id"], batch)
        for sid in batch:
            await websocket.push(sid, job["message"])
        for sid in batch:
            await send_email_with_retry(sid, job["message"], max_retries=3)

def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]
```

---

## Stage 6

### Priority Inbox

#### Approach

- Placement = 3, Result = 2, Event = 1
- Type always dominates; within same type newer wins
- Min-heap of size N → O(log N) per insertion
- Efficient for unbounded notification streams

See `notification_app_be/priority_inbox.py` for full working code.
