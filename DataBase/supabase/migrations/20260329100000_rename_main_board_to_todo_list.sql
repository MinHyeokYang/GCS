do $$
begin
  if exists (select 1 from kanban.boards where name = 'Main Board')
     and not exists (select 1 from kanban.boards where name = 'to do list') then
    update kanban.boards
    set name = 'to do list'
    where name = 'Main Board';
  end if;
end $$;

