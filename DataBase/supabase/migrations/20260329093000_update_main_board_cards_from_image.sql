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
  values ('Main Board')
  on conflict (name) do nothing;

  select id into v_board_id
  from kanban.boards
  where name = 'Main Board'
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

  insert into kanban.cards (board_id, column_id, title, position)
  values
    (v_board_id, v_backlog_id, 'api 연동하여 나만의 스니펫 작성 플랫폼 만들기', 1),
    (v_board_id, v_backlog_id, 'API 활용하여 나만의 스니펫 생성하기', 2),
    (v_board_id, v_backlog_id, '공감컴프 REVIEW', 3),
    (v_board_id, v_backlog_id, '지분희석 지시법 합격', 4),
    (v_board_id, v_backlog_id, '인간본성의 과학적 이해 지시법 합격', 5),
    (v_board_id, v_ready_id, '100일 챌린지', 1),
    (v_board_id, v_ready_id, 'AI와 스타트업 문제 해결 복습하기', 2),
    (v_board_id, v_in_progress_id, '지분희석에 대한 지시법 공부', 1),
    (v_board_id, v_in_progress_id, '인간본성의 과학적 이해 지시법 공부', 2),
    (v_board_id, v_in_progress_id, '파타고니아 인사이트 독서', 3),
    (v_board_id, v_in_review_id, '더 라스트 컴퍼니 질문 생성하기', 1),
    (v_board_id, v_done_id, '100일 챌린지 결정', 1),
    (v_board_id, v_done_id, '공감컴프 다녀오기', 2);
end $$;

