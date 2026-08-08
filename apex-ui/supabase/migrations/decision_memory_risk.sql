-- Stop-loss and quantity tracking for risk control

alter table public.decision_memory
  add column if not exists stop_loss numeric;

alter table public.decision_memory
  add column if not exists quantity numeric;
