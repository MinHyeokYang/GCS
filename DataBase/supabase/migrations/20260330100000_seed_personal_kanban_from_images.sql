do $$
declare
  v_board_id bigint;
  v_backlog_id bigint;
  v_ready_id bigint;
  v_in_progress_id bigint;
  v_in_review_id bigint;
  v_done_id bigint;
begin
  insert into kanban.boards (name)
  values ('내 일감 관리용 간반 보드')
  on conflict (name) do nothing;

  select id into v_board_id
  from kanban.boards
  where name = '내 일감 관리용 간반 보드'
  limit 1;

  perform kanban.seed_default_columns(v_board_id);

  select id into v_backlog_id
  from kanban.columns
  where board_id = v_board_id and column_key = 'backlog';

  select id into v_ready_id
  from kanban.columns
  where board_id = v_board_id and column_key = 'ready';

  select id into v_in_progress_id
  from kanban.columns
  where board_id = v_board_id and column_key = 'in_progress';

  select id into v_in_review_id
  from kanban.columns
  where board_id = v_board_id and column_key = 'in_review';

  select id into v_done_id
  from kanban.columns
  where board_id = v_board_id and column_key = 'done';

  delete from kanban.cards
  where board_id = v_board_id;

  insert into kanban.cards (board_id, column_id, title, description, position)
  values
    (v_board_id, v_backlog_id, '가계부 작성하기', 'tat01 #3', 1),
    (v_board_id, v_ready_id, '공감의 반경 읽기', 'tat01 #1', 1),
    (v_board_id, v_ready_id, '빨래 돌리기', 'tat01 #2', 2),
    (v_board_id, v_ready_id, '운동가기', 'tat01 #7', 3),
    (v_board_id, v_in_progress_id, '간반보드 만들기', 'tat01 #4', 1),
    (v_board_id, v_in_review_id, '수업 내용 복습하기', 'tat01 #5', 1),
    (v_board_id, v_done_id, '설거지 하기', 'tat01 #6', 1),
    (v_board_id, v_done_id, '쓰레기통 비우기', 'tat01 #8', 2);
end $$;

