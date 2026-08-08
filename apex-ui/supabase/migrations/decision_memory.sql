-- Decision memory for tracking outcomes and future learning (idempotent)

create table if not exists public.decision_memory (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  timestamp_ms bigint not null,
  decision_date date not null default (timezone('utc', now()))::date,
  intent text,
  stock text,
  action text not null,
  amount numeric,
  confidence numeric not null check (confidence >= 0 and confidence <= 100),
  signals jsonb,
  market_trend text,
  portfolio_snapshot jsonb,
  entry_price numeric,
  exit_price numeric,
  pnl numeric,
  success boolean,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists decision_memory_user_created_idx
  on public.decision_memory (user_id, created_at desc);

create index if not exists decision_memory_user_stock_idx
  on public.decision_memory (user_id, stock, created_at desc);

alter table public.decision_memory enable row level security;

create policy "decision_memory_select_own"
  on public.decision_memory for select
  using (auth.uid() = user_id);

create policy "decision_memory_insert_own"
  on public.decision_memory for insert
  with check (auth.uid() = user_id);

create policy "decision_memory_update_own"
  on public.decision_memory for update
  using (auth.uid() = user_id);
