-- Operating profile: investment style + intraday acknowledgment (T0 onboarding gate)

create table if not exists public.operating_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  investment_style text not null check (
    investment_style in ('long_term_only', 'core_plus_tactical', 'tactical_only')
  ),
  intraday_acknowledged_at timestamptz not null,
  updated_at timestamptz not null default now()
);

alter table public.operating_profiles enable row level security;

create policy "operating_profiles_select_own"
  on public.operating_profiles for select
  using (auth.uid() = user_id);

create policy "operating_profiles_insert_own"
  on public.operating_profiles for insert
  with check (auth.uid() = user_id);

create policy "operating_profiles_update_own"
  on public.operating_profiles for update
  using (auth.uid() = user_id);
