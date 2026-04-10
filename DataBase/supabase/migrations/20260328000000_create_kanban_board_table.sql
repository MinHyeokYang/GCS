-- migrate:up
create table if not exists public.kanban_board (
  id bigint generated always as identity primary key
);

-- migrate:down
drop table if exists public.kanban_board;
