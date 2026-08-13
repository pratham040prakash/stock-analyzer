-- Chart-backed investment journeys (per-user target paths)

create table if not exists public.investment_journeys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  symbol text not null check (char_length(symbol) <= 20),
  horizon text not null check (horizon in ('swing', 'long_term')),
  target_price_inr numeric not null check (target_price_inr > 0),
  entry_price_inr numeric check (entry_price_inr is null or entry_price_inr > 0),
  invested_amount_inr numeric check (invested_amount_inr is null or invested_amount_inr >= 0),
  started_at date not null,
  target_by date,
  target_duration_amount integer check (target_duration_amount is null or target_duration_amount > 0),
  target_duration_unit text check (
    target_duration_unit is null
    or target_duration_unit in ('days', 'weeks', 'years')
  ),
  status text not null default 'active' check (status in ('active', 'completed', 'paused')),
  notes text,
  suggested_by_apex boolean not null default false,
  chart_basis jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists investment_journeys_user_status_idx
  on public.investment_journeys (user_id, status, updated_at desc);

create unique index if not exists investment_journeys_active_symbol_idx
  on public.investment_journeys (user_id, symbol)
  where status = 'active';

alter table public.investment_journeys enable row level security;

create policy "investment_journeys_select_own"
  on public.investment_journeys for select
  using (auth.uid() = user_id);

create policy "investment_journeys_insert_own"
  on public.investment_journeys for insert
  with check (auth.uid() = user_id);

create policy "investment_journeys_update_own"
  on public.investment_journeys for update
  using (auth.uid() = user_id);
