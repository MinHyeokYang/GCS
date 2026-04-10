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
  values ('Product Roadmap')
  on conflict (name) do nothing;

  select id into v_board_id
  from kanban.boards
  where name = 'Product Roadmap'
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

  if not exists (
    select 1 from kanban.cards where board_id = v_board_id and title = '로그인 페이지 개선'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id, v_backlog_id, '로그인 페이지 개선', '에러 메시지 UX 개선',
      coalesce((select max(position) from kanban.cards where column_id = v_backlog_id), 0) + 1
    );
  end if;

  if not exists (
    select 1 from kanban.cards where board_id = v_board_id and title = 'API 응답 캐싱'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id, v_ready_id, 'API 응답 캐싱', '자주 조회되는 목록 캐시 도입',
      coalesce((select max(position) from kanban.cards where column_id = v_ready_id), 0) + 1
    );
  end if;

  if not exists (
    select 1 from kanban.cards where board_id = v_board_id and title = '칸반 드래그 버그 수정'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id, v_in_progress_id, '칸반 드래그 버그 수정', '모바일에서 드래그 끊김 수정',
      coalesce((select max(position) from kanban.cards where column_id = v_in_progress_id), 0) + 1
    );
  end if;

  if not exists (
    select 1 from kanban.cards where board_id = v_board_id and title = '결제 모듈 코드리뷰'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id, v_in_review_id, '결제 모듈 코드리뷰', '리팩터링 PR 검토',
      coalesce((select max(position) from kanban.cards where column_id = v_in_review_id), 0) + 1
    );
  end if;

  if not exists (
    select 1 from kanban.cards where board_id = v_board_id and title = '초기 ERD 작성'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id, v_done_id, '초기 ERD 작성', '도메인 모델 및 관계 정의 완료',
      coalesce((select max(position) from kanban.cards where column_id = v_done_id), 0) + 1
    );
  end if;
end $$;

