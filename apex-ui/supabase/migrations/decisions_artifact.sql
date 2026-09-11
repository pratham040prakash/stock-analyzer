-- Wave 1 additive migration: immutable daily decision artifact authority.
-- Apply manually after decisions_history.sql. Legacy columns remain for compatibility.

alter table public.decisions
  add column if not exists artifact jsonb,
  add column if not exists frozen_at timestamptz,
  add column if not exists schema_version text,
  add column if not exists intent text;

alter table public.decisions
  drop constraint if exists decisions_decision_check;

alter table public.decisions
  add constraint decisions_decision_check
  check (decision in ('BUY_MORE', 'HOLD', 'REDUCE', 'WAIT', 'EXPLORE'));

drop policy if exists "decisions_update_own" on public.decisions;
create policy "decisions_update_own"
  on public.decisions for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

