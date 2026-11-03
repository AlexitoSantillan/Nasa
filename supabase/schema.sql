create table if not exists public.lecturas (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  astronauta      text,
  ritmo_cardiaco  numeric,
  spo2            numeric,
  temperatura     numeric,
  movimiento      numeric,
  sueno_horas     numeric,
  estres          numeric,
  ejercicio_min   numeric,
  radiacion       numeric,
  estado          text,
  recomendacion   text
);

create index if not exists lecturas_created_at_idx on public.lecturas (created_at desc);

alter table public.lecturas enable row level security;

-- La web 3D (clave publishable/anon) solo puede LEER.
drop policy if exists "lectura publica" on public.lecturas;
create policy "lectura publica" on public.lecturas
  for select to anon using (true);

-- Permisos explícitos (algunos proyectos nuevos no los dan solos)
grant usage on schema public to anon, service_role;
grant select on public.lecturas to anon;
grant all on public.lecturas to service_role;
grant usage, select on all sequences in schema public to service_role;

-- Refresca la caché de la API para que vea la tabla enseguida
notify pgrst, 'reload schema';