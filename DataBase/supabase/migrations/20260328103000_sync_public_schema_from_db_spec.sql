create table if not exists public.department (
  department_id serial primary key,
  department_name text unique,
  founded_date date not null,
  office_phone text,
  office_address text,
  note text
);

create table if not exists public.student (
  student_id serial primary key,
  name text not null,
  birth_date date not null,
  phone text unique,
  email text unique,
  department_id int,
  note text
);

create table if not exists public.course (
  course_id serial primary key,
  course_name text not null,
  note text
);

create table if not exists public.enrollment (
  enrollment_id serial primary key,
  student_id int,
  course_id int,
  gpa numeric(4,2),
  note text
);

do $$
begin
  if not exists (
    select 1
    from information_schema.table_constraints
    where constraint_schema = 'public'
      and table_name = 'student'
      and constraint_name = 'student_department_id_fkey'
  ) then
    alter table public.student
      add constraint student_department_id_fkey
      foreign key (department_id) references public.department(department_id);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from information_schema.table_constraints
    where constraint_schema = 'public'
      and table_name = 'enrollment'
      and constraint_name = 'enrollment_student_id_fkey'
  ) then
    alter table public.enrollment
      add constraint enrollment_student_id_fkey
      foreign key (student_id) references public.student(student_id);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from information_schema.table_constraints
    where constraint_schema = 'public'
      and table_name = 'enrollment'
      and constraint_name = 'enrollment_course_id_fkey'
  ) then
    alter table public.enrollment
      add constraint enrollment_course_id_fkey
      foreign key (course_id) references public.course(course_id);
  end if;
end $$;
