-- Pega esto en Supabase -> SQL Editor -> Run
create table if not exists public.lecturas (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  astronauta      text,
  ritmo_cardiaco  numeric,
  spo2            numeric,
  temperatura     numeric,
  movimiento      numeric,
  estado          text,
  recomendacion   text
);

alter table public.lecturas enable row level security;

-- La web 3D (clave publishable/anon) solo puede LEER.
drop policy if exists "lectura publica" on public.lecturas;
create policy "lectura publica" on public.lecturas
  for select to anon using (true);

-- Escribir lo hace solo la API de Render con la clave secreta (que ignora RLS).
