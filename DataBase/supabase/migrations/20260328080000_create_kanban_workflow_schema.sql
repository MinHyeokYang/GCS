create schema if not exists kanban;

create table if not exists kanban.boards (
  id bigint generated always as identity primary key,
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists kanban.columns (
  id bigint generated always as identity primary key,
  board_id bigint not null references kanban.boards(id) on delete cascade,
  column_key text not null check (column_key in ('backlog', 'ready', 'in_progress', 'in_review', 'done')),
  title text not null,
  ordinal int not null check (ordinal between 1 and 5),
  created_at timestamptz not null default now(),
  unique (board_id, column_key),
  unique (board_id, ordinal)
);

create table if not exists kanban.cards (
  id bigint generated always as identity primary key,
  board_id bigint not null references kanban.boards(id) on delete cascade,
  column_id bigint not null references kanban.columns(id) on delete restrict,
  title text not null,
  description text,
  position int not null check (position > 0),
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (column_id, position)
);

create index if not exists idx_kanban_cards_board_column_position
  on kanban.cards(board_id, column_id, position);

create table if not exists kanban.card_history (
  id bigint generated always as identity primary key,
  card_id bigint not null references kanban.cards(id) on delete cascade,
  board_id bigint not null references kanban.boards(id) on delete cascade,
  from_column_id bigint not null references kanban.columns(id) on delete restrict,
  to_column_id bigint not null references kanban.columns(id) on delete restrict,
  moved_by uuid,
  moved_at timestamptz not null default now()
);

create or replace function kanban.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_kanban_cards_set_updated_at on kanban.cards;
create trigger trg_kanban_cards_set_updated_at
before update on kanban.cards
for each row
execute function kanban.set_updated_at();

create or replace function kanban.seed_default_columns(p_board_id bigint)
returns void
language plpgsql
as $$
begin
  insert into kanban.columns (board_id, column_key, title, ordinal)
  values
    (p_board_id, 'backlog', 'Backlog', 1),
    (p_board_id, 'ready', 'Ready', 2),
    (p_board_id, 'in_progress', 'In Progress', 3),
    (p_board_id, 'in_review', 'In Review', 4),
    (p_board_id, 'done', 'Done', 5)
  on conflict (board_id, column_key) do nothing;
end;
$$;

create or replace function kanban.trg_seed_columns_after_board_insert()
returns trigger
language plpgsql
as $$
begin
  perform kanban.seed_default_columns(new.id);
  return new;
end;
$$;

drop trigger if exists trg_seed_columns_after_board_insert on kanban.boards;
create trigger trg_seed_columns_after_board_insert
after insert on kanban.boards
for each row
execute function kanban.trg_seed_columns_after_board_insert();

create or replace function kanban.move_card(
  p_card_id bigint,
  p_to_column_key text,
  p_actor_id uuid default null
)
returns kanban.cards
language plpgsql
as $$
declare
  v_card kanban.cards%rowtype;
  v_from_column kanban.columns%rowtype;
  v_to_column kanban.columns%rowtype;
  v_new_position int;
begin
  select *
    into v_card
  from kanban.cards
  where id = p_card_id
  for update;

  if not found then
    raise exception 'Card % not found', p_card_id;
  end if;

  select *
    into v_from_column
  from kanban.columns
  where id = v_card.column_id;

  if not found then
    raise exception 'Source column for card % not found', p_card_id;
  end if;

  select *
    into v_to_column
  from kanban.columns
  where board_id = v_card.board_id
    and column_key = p_to_column_key;

  if not found then
    raise exception 'Target column % not found in board %', p_to_column_key, v_card.board_id;
  end if;

  if v_to_column.id = v_from_column.id then
    return v_card;
  end if;

  if v_to_column.ordinal <> v_from_column.ordinal + 1 then
    raise exception 'Invalid transition: % -> %. Allowed only next step.',
      v_from_column.column_key, v_to_column.column_key;
  end if;

  select coalesce(max(position), 0) + 1
    into v_new_position
  from kanban.cards
  where column_id = v_to_column.id;

  update kanban.cards
  set column_id = v_to_column.id,
      position = v_new_position,
      updated_at = now()
  where id = v_card.id;

  with ranked as (
    select id, row_number() over (order by position, id) as rn
    from kanban.cards
    where column_id = v_from_column.id
  )
  update kanban.cards c
  set position = ranked.rn
  from ranked
  where c.id = ranked.id
    and c.position <> ranked.rn;

  insert into kanban.card_history (
    card_id, board_id, from_column_id, to_column_id, moved_by
  ) values (
    v_card.id, v_card.board_id, v_from_column.id, v_to_column.id, p_actor_id
  );

  select *
    into v_card
  from kanban.cards
  where id = p_card_id;

  return v_card;
end;
$$;

insert into kanban.boards (name)
select 'Main Board'
where not exists (
  select 1 from kanban.boards where name = 'Main Board'
);

