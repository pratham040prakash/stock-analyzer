-- APEX production schema (run in Supabase SQL editor)

create table if not exists public.broker_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  broker text not null default 'zerodha',
  access_token text not null,
  public_token text,
  access_token_encrypted text,
  public_token_encrypted text,
  kite_user_id text,
  status text not null default 'active' check (status in ('active', 'expired', 'revoked')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, broker)
);

-- Legacy column names (optional upgrade path):
-- alter table public.broker_connections add column if not exists access_token text;
-- alter table public.broker_connections add column if not exists public_token text;
-- alter table public.broker_connections add column if not exists access_token_encrypted text;
-- alter table public.broker_connections add column if not exists public_token_encrypted text;
-- alter table public.broker_connections add column if not exists kite_user_id text;

create table if not exists public.portfolio_snapshots (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  holdings jsonb not null default '[]'::jsonb,
  total_value numeric not null default 0,
  pnl numeric not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists portfolio_snapshots_user_created_idx
  on public.portfolio_snapshots (user_id, created_at desc);

create table if not exists public.financial_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  income_range text not null,
  expense_range text not null,
  investable_surplus numeric not null default 0,
  auto_trading_enabled boolean not null default false,
  updated_at timestamptz not null default now()
);

create table if not exists public.mentor_outputs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  decision jsonb not null,
  message text not null,
  confidence text not null check (confidence in ('low', 'medium', 'high')),
  created_at timestamptz not null default now()
);

create index if not exists mentor_outputs_user_created_idx
  on public.mentor_outputs (user_id, created_at desc);

create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  decision_date date not null default (timezone('utc', now()))::date,
  decision text not null check (decision in ('BUY_MORE', 'HOLD', 'REDUCE', 'WAIT')),
  action text not null default 'hold',
  stock text,
  confidence numeric not null check (confidence >= 0 and confidence <= 100),
  reason text not null,
  actions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (user_id, decision_date)
);

create index if not exists decisions_user_created_idx
  on public.decisions (user_id, created_at desc);

create index if not exists decisions_user_decision_date_idx
  on public.decisions (user_id, decision_date desc);

alter table public.broker_connections enable row level security;
alter table public.portfolio_snapshots enable row level security;
alter table public.financial_profiles enable row level security;
alter table public.mentor_outputs enable row level security;
alter table public.decisions enable row level security;

create policy "broker_connections_select_own"
  on public.broker_connections for select
  using (auth.uid() = user_id);

create policy "broker_connections_insert_own"
  on public.broker_connections for insert
  with check (auth.uid() = user_id);

create policy "broker_connections_update_own"
  on public.broker_connections for update
  using (auth.uid() = user_id);

create policy "portfolio_snapshots_select_own"
  on public.portfolio_snapshots for select
  using (auth.uid() = user_id);

create policy "portfolio_snapshots_insert_own"
  on public.portfolio_snapshots for insert
  with check (auth.uid() = user_id);

create policy "financial_profiles_select_own"
  on public.financial_profiles for select
  using (auth.uid() = user_id);

create policy "financial_profiles_insert_own"
  on public.financial_profiles for insert
  with check (auth.uid() = user_id);

create policy "financial_profiles_update_own"
  on public.financial_profiles for update
  using (auth.uid() = user_id);

create policy "mentor_outputs_select_own"
  on public.mentor_outputs for select
  using (auth.uid() = user_id);

create policy "mentor_outputs_insert_own"
  on public.mentor_outputs for insert
  with check (auth.uid() = user_id);

create policy "decisions_select_own"
  on public.decisions for select
  using (auth.uid() = user_id);

create policy "decisions_insert_own"
  on public.decisions for insert
  with check (auth.uid() = user_id);

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
  stop_loss numeric,
  quantity numeric,
  take_profit_taken boolean not null default false,
  pnl numeric,
  success boolean,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists decision_memory_user_created_idx
  on public.decision_memory (user_id, created_at desc);

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
