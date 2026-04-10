do $$
begin
  if exists (select 1 from kanban.boards where name = '내 일감 관리용 간반 보드')
     and not exists (select 1 from kanban.boards where name = '양민혁') then
    update kanban.boards
    set name = '양민혁'
    where name = '내 일감 관리용 간반 보드';
  end if;

  if exists (select 1 from kanban.boards where name = 'to do list')
     and not exists (select 1 from kanban.boards where name = '김태호') then
    update kanban.boards
    set name = '김태호'
    where name = 'to do list';
  end if;

  if exists (select 1 from kanban.boards where name = '4월 메인 프로젝트 성공 시키기')
     and not exists (select 1 from kanban.boards where name = '이건후') then
    update kanban.boards
    set name = '이건후'
    where name = '4월 메인 프로젝트 성공 시키기';
  end if;
end $$;

