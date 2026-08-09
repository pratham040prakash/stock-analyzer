-- Premium access activations (PREMIUM-002, no billing)

create table if not exists public.premium_activations (
  user_id uuid primary key references auth.users(id) on delete cascade,
  code_label text not null,
  activated_at timestamptz not null default now()
);

create index if not exists premium_activations_activated_at_idx
  on public.premium_activations (activated_at desc);

alter table public.premium_activations enable row level security;

do $$
begin
  create policy "premium_activations_select_own"
    on public.premium_activations for select
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;
