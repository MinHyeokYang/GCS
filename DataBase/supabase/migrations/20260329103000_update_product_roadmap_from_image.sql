do $$
declare
  v_board_id bigint;
  v_backlog_id bigint;
  v_ready_id bigint;
  v_in_progress_id bigint;
  v_in_review_id bigint;
  v_done_id bigint;
begin
  if exists (select 1 from kanban.boards where name = 'Product Roadmap') then
    update kanban.boards
    set name = '4월 메인 프로젝트 성공 시키기'
    where name = 'Product Roadmap';
  end if;

  insert into kanban.boards (name)
  values ('4월 메인 프로젝트 성공 시키기')
  on conflict (name) do nothing;

  select id into v_board_id
  from kanban.boards
  where name = '4월 메인 프로젝트 성공 시키기'
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

  update kanban.columns
  set title = 'To do'
  where id = v_ready_id;

  delete from kanban.cards
  where board_id = v_board_id;

  insert into kanban.cards (board_id, column_id, title, position)
  values
    (v_board_id, v_backlog_id, '4월 메인 프로젝트의 성공', 1),
    (v_board_id, v_backlog_id, '4월 메인 프로젝트를 위한 역량 강화', 2),
    (v_board_id, v_ready_id, '0. 4월 메인 프로젝트 구체화', 1),
    (v_board_id, v_ready_id, '1. 대상 고객 선정', 2),
    (v_board_id, v_ready_id, '2. 고객 문제 정의', 3),
    (v_board_id, v_ready_id, '3. 고유가치 제안(UVP) 설정', 4),
    (v_board_id, v_ready_id, '4. 솔루션 도출', 5),
    (v_board_id, v_ready_id, '5. 수익 모델 설정', 6),
    (v_board_id, v_ready_id, '6. 채널, BEP, 3년간 손익계획, KPI 설정', 7),
    (v_board_id, v_in_progress_id, 'DB 팀 프로젝트', 1),
    (v_board_id, v_in_progress_id, '(사회적 가치) 사회적 기업 학습 by 파타고니아', 2),
    (v_board_id, v_in_review_id, '(세미나) 엠비디아 책 내용 복습', 1),
    (v_board_id, v_in_review_id, '(인사와 조직) 나 사용 설명서 구체화', 2),
    (v_board_id, v_done_id, '지배는 랜딩페이지 팀 프로젝트', 1),
    (v_board_id, v_done_id, 'API 팀 프로젝트', 2),
    (v_board_id, v_done_id, '(UX) 고객 인터뷰 팀 프로젝트', 3);
end $$;

