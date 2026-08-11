-- Premium trial offers (T3-3 conversion funnel)

create table if not exists public.premium_trial_offers (
  user_id uuid primary key references auth.users(id) on delete cascade,
  trigger_receipt_id uuid not null,
  offered_at timestamptz not null default now(),
  claimed_at timestamptz,
  expires_at timestamptz,
  dismissed_at timestamptz
);

create index if not exists premium_trial_offers_expires_at_idx
  on public.premium_trial_offers (expires_at desc);

alter table public.premium_trial_offers enable row level security;

do $$
begin
  create policy "premium_trial_offers_select_own"
    on public.premium_trial_offers for select
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;
