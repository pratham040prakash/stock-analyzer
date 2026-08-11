-- Razorpay subscription records (T3-2 billing)

create table if not exists public.premium_subscriptions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  razorpay_subscription_id text not null unique,
  razorpay_plan_id text not null,
  billing_interval text not null check (billing_interval in ('monthly', 'yearly')),
  status text not null,
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists premium_subscriptions_status_idx
  on public.premium_subscriptions (status);

create index if not exists premium_subscriptions_period_end_idx
  on public.premium_subscriptions (current_period_end desc);

alter table public.premium_subscriptions enable row level security;

do $$
begin
  create policy "premium_subscriptions_select_own"
    on public.premium_subscriptions for select
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;
