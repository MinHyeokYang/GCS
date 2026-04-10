do $$
declare
  v_board_id bigint;
  v_backlog_id bigint;
  v_ready_id bigint;
  v_in_progress_id bigint;
  v_in_review_id bigint;
  v_done_id bigint;
  v_card_id bigint;
begin
  insert into kanban.boards (name)
  values ('Main Board')
  on conflict (name) do nothing;

  select id into v_board_id
  from kanban.boards
  where name = 'Main Board';

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
    select 1
    from kanban.cards
    where board_id = v_board_id and title = '요구사항 정리'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_backlog_id,
      '요구사항 정리',
      '프로젝트 범위와 MVP 정의',
      coalesce((select max(position) from kanban.cards where column_id = v_backlog_id), 0) + 1
    );
  end if;

  if not exists (
    select 1
    from kanban.cards
    where board_id = v_board_id and title = 'API 명세 초안 작성'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_ready_id,
      'API 명세 초안 작성',
      '카드 생성/이동/조회 엔드포인트 설계',
      coalesce((select max(position) from kanban.cards where column_id = v_ready_id), 0) + 1
    );
  end if;

  if not exists (
    select 1
    from kanban.cards
    where board_id = v_board_id and title = '드래그앤드롭 UI 구현'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_in_progress_id,
      '드래그앤드롭 UI 구현',
      '컬럼 간 카드 이동 인터랙션 구현',
      coalesce((select max(position) from kanban.cards where column_id = v_in_progress_id), 0) + 1
    );
  end if;

  if not exists (
    select 1
    from kanban.cards
    where board_id = v_board_id and title = 'PR 리뷰 반영'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_in_review_id,
      'PR 리뷰 반영',
      '코드리뷰 코멘트 수정 및 재검토 요청',
      coalesce((select max(position) from kanban.cards where column_id = v_in_review_id), 0) + 1
    );
  end if;

  if not exists (
    select 1
    from kanban.cards
    where board_id = v_board_id and title = 'DB 스키마 마이그레이션'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_done_id,
      'DB 스키마 마이그레이션',
      '초기 테이블 및 인덱스 생성 완료',
      coalesce((select max(position) from kanban.cards where column_id = v_done_id), 0) + 1
    );
  end if;

  if not exists (
    select 1
    from kanban.cards
    where board_id = v_board_id and title = '인증 미들웨어 연결'
  ) then
    insert into kanban.cards (board_id, column_id, title, description, position)
    values (
      v_board_id,
      v_backlog_id,
      '인증 미들웨어 연결',
      'JWT 검증 및 권한 체크 추가',
      coalesce((select max(position) from kanban.cards where column_id = v_backlog_id), 0) + 1
    )
    returning id into v_card_id;

    perform kanban.move_card(v_card_id, 'ready', null);
  end if;
end $$;

