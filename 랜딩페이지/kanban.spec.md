# Supabase Kanban Schema

## boards

| Column Name | Type        | Constraint |
| ----------- | ----------- | ---------- |
| id          | BIGINT      | PK         |
| name        | TEXT        | UK         |
| created_at  | TIMESTAMPTZ | NOT NULL   |

---

## columns

| Column Name | Type        | Constraint                                |
| ----------- | ----------- | ----------------------------------------- |
| id          | BIGINT      | PK                                        |
| board_id    | BIGINT      | FK -> boards(id)                          |
| column_key  | TEXT        | CHECK(backlog/ready/in_progress/in_review/done) |
| title       | TEXT        | NOT NULL                                  |
| ordinal     | INT         | CHECK(1~5), UK(with board_id)             |
| created_at  | TIMESTAMPTZ | NOT NULL                                  |

---

## cards

| Column Name | Type        | Constraint                   |
| ----------- | ----------- | ---------------------------- |
| id          | BIGINT      | PK                           |
| board_id    | BIGINT      | FK -> boards(id)             |
| column_id   | BIGINT      | FK -> columns(id)            |
| title       | TEXT        | NOT NULL                     |
| description | TEXT        | Nullable                     |
| position    | INT         | NOT NULL, UK(with column_id) |
| created_by  | UUID        | Nullable                     |
| created_at  | TIMESTAMPTZ | NOT NULL                     |
| updated_at  | TIMESTAMPTZ | NOT NULL                     |

---

## card_history

| Column Name    | Type        | Constraint              |
| -------------- | ----------- | ----------------------- |
| id             | BIGINT      | PK                      |
| card_id        | BIGINT      | FK -> cards(id)         |
| board_id       | BIGINT      | FK -> boards(id)        |
| from_column_id | BIGINT      | FK -> columns(id)       |
| to_column_id   | BIGINT      | FK -> columns(id)       |
| moved_by       | UUID        | Nullable                |
| moved_at       | TIMESTAMPTZ | NOT NULL                |
