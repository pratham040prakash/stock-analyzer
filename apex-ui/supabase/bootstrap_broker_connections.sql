-- Minimal bootstrap: safe to re-run (idempotent).
-- Project: wmgnwujrtsmtchuhcfzk
-- https://supabase.com/dashboard/project/wmgnwujrtsmtchuhcfzk/sql/new

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

alter table public.broker_connections enable row level security;

drop policy if exists "broker_connections_select_own" on public.broker_connections;
create policy "broker_connections_select_own"
  on public.broker_connections for select
  using (auth.uid() = user_id);

drop policy if exists "broker_connections_insert_own" on public.broker_connections;
create policy "broker_connections_insert_own"
  on public.broker_connections for insert
  with check (auth.uid() = user_id);

drop policy if exists "broker_connections_update_own" on public.broker_connections;
create policy "broker_connections_update_own"
  on public.broker_connections for update
  using (auth.uid() = user_id);

-- Ensure columns expected by the app exist (safe if already present)
alter table public.broker_connections add column if not exists access_token text;
alter table public.broker_connections add column if not exists public_token text;
alter table public.broker_connections add column if not exists access_token_encrypted text;
alter table public.broker_connections add column if not exists public_token_encrypted text;
alter table public.broker_connections add column if not exists kite_user_id text;
alter table public.broker_connections add column if not exists status text default 'active';
alter table public.broker_connections add column if not exists created_at timestamptz default now();
alter table public.broker_connections add column if not exists updated_at timestamptz default now();

-- Backfill status for any existing rows
update public.broker_connections set status = 'active' where status is null;

-- Required for upsert on (user_id, broker)
create unique index if not exists broker_connections_user_id_broker_key
  on public.broker_connections (user_id, broker);
