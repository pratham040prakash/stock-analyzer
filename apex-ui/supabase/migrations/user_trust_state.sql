-- Trust score + last closed-trade outcome (OUTCOME-001)

alter table public.decision_memory
  add column if not exists trust_evaluated_at timestamptz;

create index if not exists decision_memory_trust_pending_idx
  on public.decision_memory (user_id, updated_at desc)
  where exit_price is not null and trust_evaluated_at is null;

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

create policy "user_trust_state_select_own"
  on public.user_trust_state for select
  using (auth.uid() = user_id);

create policy "user_trust_state_insert_own"
  on public.user_trust_state for insert
  with check (auth.uid() = user_id);

create policy "user_trust_state_update_own"
  on public.user_trust_state for update
  using (auth.uid() = user_id);
