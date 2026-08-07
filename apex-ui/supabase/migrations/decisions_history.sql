-- Extend decisions table for daily history tracking (idempotent)

alter table public.decisions
  add column if not exists decision_date date;

alter table public.decisions
  add column if not exists action text;

alter table public.decisions
  add column if not exists stock text;

update public.decisions
set decision_date = (created_at at time zone 'UTC')::date
where decision_date is null;

create unique index if not exists decisions_user_date_key
  on public.decisions (user_id, decision_date);

create index if not exists decisions_user_decision_date_idx
  on public.decisions (user_id, decision_date desc);
