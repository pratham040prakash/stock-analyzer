-- Discipline streak state + daily commits (DISCIPLINE-001)

create table if not exists public.discipline_streak_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  streak_count integer not null default 0 check (streak_count >= 0),
  last_commit_date date,
  last_decision_key text,
  last_action_followed boolean not null default false,
  updated_at timestamptz not null default now()
);

create table if not exists public.discipline_commits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  commit_date date not null,
  intent text not null,
  action text not null,
  stock text,
  decision_key text not null,
  followed boolean not null default true,
  streak_count integer not null default 0 check (streak_count >= 0),
  created_at timestamptz not null default now(),
  unique (user_id, commit_date)
);

create index if not exists discipline_commits_user_date_idx
  on public.discipline_commits (user_id, commit_date desc);

alter table public.discipline_streak_state enable row level security;
alter table public.discipline_commits enable row level security;

create policy "discipline_streak_state_select_own"
  on public.discipline_streak_state for select
  using (auth.uid() = user_id);

create policy "discipline_streak_state_insert_own"
  on public.discipline_streak_state for insert
  with check (auth.uid() = user_id);

create policy "discipline_streak_state_update_own"
  on public.discipline_streak_state for update
  using (auth.uid() = user_id);

create policy "discipline_commits_select_own"
  on public.discipline_commits for select
  using (auth.uid() = user_id);

create policy "discipline_commits_insert_own"
  on public.discipline_commits for insert
  with check (auth.uid() = user_id);

create policy "discipline_commits_update_own"
  on public.discipline_commits for update
  using (auth.uid() = user_id);
