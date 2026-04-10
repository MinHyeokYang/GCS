-- migrate:up
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
  department_id int references public.department(department_id),
  note text
);

create table if not exists public.course (
  course_id serial primary key,
  course_name text not null,
  note text
);

create table if not exists public.enrollment (
  enrollment_id serial primary key,
  student_id int references public.student(student_id),
  course_id int references public.course(course_id),
  gpa numeric(4,2),
  note text
);

-- migrate:down
drop table if exists public.enrollment;
drop table if exists public.course;
drop table if exists public.student;
drop table if exists public.department;
