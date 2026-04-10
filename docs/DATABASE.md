# DATABASE - Team Todo DB 명세

업데이트: 2026-04-10

## 1. 저장소 구성
- DBMS: SQLite
- ORM: SQLAlchemy 2.x
- 기본 파일: `./todo.db`

## 2. ERD(요약)
```text
User ---< TeamMember >--- Team ---< Todo ---< TodoTag >--- Tag
                           |
                           +---< Todo ---< Comment >--- User
```

## 3. 테이블 정의

### users
- `id` PK
- `name` varchar(100) not null
- `email` varchar(255) unique not null
- `created_at` datetime not null

### teams
- `id` PK
- `name` varchar(100) not null
- `created_at` datetime not null

### team_members
- `team_id` PK/FK -> teams.id (`ON DELETE CASCADE`)
- `user_id` PK/FK -> users.id (`ON DELETE CASCADE`)
- `joined_at` datetime not null

### todos
- `id` PK
- `title` varchar(255) not null
- `description` text null
- `status` varchar(20) not null (`todo`/`in_progress`/`done`)
- `priority` varchar(10) not null (`low`/`medium`/`high`)
- `due_date` date null
- `team_id` FK -> teams.id (`ON DELETE CASCADE`)
- `assignee_id` FK -> users.id (`ON DELETE SET NULL`)
- `created_by` FK -> users.id (`ON DELETE RESTRICT`)
- `created_at` datetime not null
- `updated_at` datetime not null

### tags
- `id` PK
- `name` varchar(50) not null
- `team_id` FK -> teams.id (`ON DELETE CASCADE`)
- unique(`name`, `team_id`)

### todo_tags
- `todo_id` PK/FK -> todos.id (`ON DELETE CASCADE`)
- `tag_id` PK/FK -> tags.id (`ON DELETE CASCADE`)

### comments
- `id` PK
- `todo_id` FK -> todos.id (`ON DELETE CASCADE`)
- `user_id` FK -> users.id (`ON DELETE CASCADE`)
- `content` text not null
- `created_at` datetime not null
- `updated_at` datetime not null

## 4. 참조 무결성 규칙
- Todo 삭제 시 연결된 Comment/TodoTag도 함께 삭제
- User 삭제 시 TeamMember/Comment는 삭제
- User가 `todos.created_by`로 참조 중이면 삭제 차단(`RESTRICT`)
