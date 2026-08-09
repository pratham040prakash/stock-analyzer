-- Trust score + last closed-trade outcome (OUTCOME-001)
-- Bootstraps decision_memory when missing, then adds trust tracking.

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
  trust_evaluated_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.decision_memory
  add column if not exists stop_loss numeric;

alter table public.decision_memory
  add column if not exists quantity numeric;

alter table public.decision_memory
  add column if not exists take_profit_taken boolean not null default false;

alter table public.decision_memory
  add column if not exists trust_evaluated_at timestamptz;

create index if not exists decision_memory_user_created_idx
  on public.decision_memory (user_id, created_at desc);

create index if not exists decision_memory_user_stock_idx
  on public.decision_memory (user_id, stock, created_at desc);

create index if not exists decision_memory_trust_pending_idx
  on public.decision_memory (user_id, updated_at desc)
  where exit_price is not null and trust_evaluated_at is null;

alter table public.decision_memory enable row level security;

do $$
begin
  create policy "decision_memory_select_own"
    on public.decision_memory for select
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create policy "decision_memory_insert_own"
    on public.decision_memory for insert
    with check (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create policy "decision_memory_update_own"
    on public.decision_memory for update
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

create table if not exists public.user_trust_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  trust_score integer not null default 50 check (trust_score >= 0 and trust_score <= 100),
  last_trust_delta integer not null default 0,
  last_outcome jsonb,
  last_decision_id uuid,
  last_closed_at timestamptz,
  last_stock text,
  updated_at timestamptz not null default now()
);

alter table public.user_trust_state enable row level security;

do $$
begin
  create policy "user_trust_state_select_own"
    on public.user_trust_state for select
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create policy "user_trust_state_insert_own"
    on public.user_trust_state for insert
    with check (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create policy "user_trust_state_update_own"
    on public.user_trust_state for update
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;
