do $$
declare
  v_cs_id int;
  v_math_id int;
  v_db_course_id int;
  v_ai_course_id int;
  v_student_1_id int;
  v_student_2_id int;
begin
  insert into public.department (department_name, founded_date, office_phone, office_address, note)
  values ('Computer Science', '2010-03-02', '02-1111-2222', 'Building A', 'Core engineering department')
  on conflict (department_name) do update
    set founded_date = excluded.founded_date
  returning department_id into v_cs_id;

  insert into public.department (department_name, founded_date, office_phone, office_address, note)
  values ('Mathematics', '2008-03-03', '02-3333-4444', 'Building B', 'Applied and pure mathematics')
  on conflict (department_name) do update
    set founded_date = excluded.founded_date
  returning department_id into v_math_id;

  if not exists (
    select 1 from public.course where course_name = 'Database Systems'
  ) then
    insert into public.course (course_name, note)
    values ('Database Systems', 'Relational modeling and SQL');
  end if;

  if not exists (
    select 1 from public.course where course_name = 'Introduction to AI'
  ) then
    insert into public.course (course_name, note)
    values ('Introduction to AI', 'Basics of machine learning');
  end if;

  select course_id into v_db_course_id
  from public.course
  where course_name = 'Database Systems'
  order by course_id
  limit 1;

  select course_id into v_ai_course_id
  from public.course
  where course_name = 'Introduction to AI'
  order by course_id
  limit 1;

  insert into public.student (name, birth_date, phone, email, department_id, note)
  values ('Kim Minho', '2004-05-12', '010-1000-2000', 'minho.kim@example.com', v_cs_id, 'Interested in backend')
  on conflict (email) do update
    set name = excluded.name,
        department_id = excluded.department_id
  returning student_id into v_student_1_id;

  insert into public.student (name, birth_date, phone, email, department_id, note)
  values ('Lee Jisoo', '2003-11-03', '010-3000-4000', 'jisoo.lee@example.com', v_math_id, 'Interested in data analysis')
  on conflict (email) do update
    set name = excluded.name,
        department_id = excluded.department_id
  returning student_id into v_student_2_id;

  if not exists (
    select 1
    from public.enrollment
    where student_id = v_student_1_id and course_id = v_db_course_id
  ) then
    insert into public.enrollment (student_id, course_id, gpa, note)
    values (v_student_1_id, v_db_course_id, 3.85, 'Spring semester');
  end if;

  if not exists (
    select 1
    from public.enrollment
    where student_id = v_student_2_id and course_id = v_ai_course_id
  ) then
    insert into public.enrollment (student_id, course_id, gpa, note)
    values (v_student_2_id, v_ai_course_id, 3.92, 'Spring semester');
  end if;
end $$;
