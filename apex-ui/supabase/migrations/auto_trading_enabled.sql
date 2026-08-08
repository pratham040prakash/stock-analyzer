-- Auto-trading preference (default off)

alter table public.financial_profiles
  add column if not exists auto_trading_enabled boolean not null default false;
