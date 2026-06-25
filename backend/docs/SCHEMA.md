# Database Schema

## Relational DB (SQLite)

### `users`

| Column         | Type | Constraints        | Description        |
|----------------|------|--------------------|--------------------|
| id             | TEXT | PRIMARY KEY        | UUID               |
| email          | TEXT | UNIQUE NOT NULL    | Login email        |
| password_hash  | TEXT | NOT NULL           | bcrypt hash        |
| created_at     | TEXT | NOT NULL           | ISO 8601 UTC       |

### `notes`

| Column       | Type    | Constraints              | Description              |
|--------------|---------|--------------------------|--------------------------|
| id           | TEXT    | PRIMARY KEY              | UUID                     |
| user_id      | TEXT    | NOT NULL, FK → users(id) | Owner                    |
| title        | TEXT    | NOT NULL                 | Note title               |
| content      | TEXT    | NOT NULL                 | Full markdown/text body  |
| file_type    | TEXT    | DEFAULT 'md'             | md / txt                 |
| content_hash | TEXT    | NOT NULL                 | SHA-256 of content       |
| chunk_count  | INTEGER | DEFAULT 0                | Chroma chunk count       |
| created_at   | TEXT    | NOT NULL                 | ISO 8601 UTC             |
| updated_at   | TEXT    | NOT NULL                 | ISO 8601 UTC             |

**Security:** Every query on `notes` MUST include `WHERE user_id = ?`.

Unique index: `(user_id, content_hash)` — duplicate content per user is rejected on create.

---

## Vector DB (ChromaDB)

**Collection name:** `notes`

| Field       | Description                                      |
|-------------|--------------------------------------------------|
| `id`        | `{note_id}-{chunk_index}`                        |
| `document`  | Chunk text                                       |
| `embedding` | BGE vector (384-dim for bge-small-zh-v1.5)       |
| `metadata`  | See below                                        |

### Chunk metadata

```json
{
  "note_id": "uuid",
  "user_id": "uuid",
  "note_title": "string",
  "chunk_index": 0
}
```

**Security:** Every vector search MUST use Chroma `where`:

```python
where={"user_id": current_user_id}
```

This ensures users only retrieve their own note chunks.
