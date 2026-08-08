-- Partial take-profit tracking for profit optimization

alter table public.decision_memory
  add column if not exists take_profit_taken boolean not null default false;
