create table if not exists public.life_bank_consents (
  user_id uuid primary key references auth.users(id) on delete cascade,
  consent_id text not null unique,
  status text not null check (
    status in ('pending', 'active', 'fetched', 'failed', 'rejected')
  ),
  mobile_last4 text not null default '',
  salary_inr integer not null default 0,
  needs_inr integer not null default 0,
  leaks_inr integer not null default 0,
  emi_inr integer not null default 0,
  row_count integer not null default 0,
  fetched_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.life_bank_consents enable row level security;

create policy "life_bank_consents_select_own"
  on public.life_bank_consents for select
  using (auth.uid() = user_id);

create policy "life_bank_consents_insert_own"
  on public.life_bank_consents for insert
  with check (auth.uid() = user_id);

create policy "life_bank_consents_update_own"
  on public.life_bank_consents for update
  using (auth.uid() = user_id);
