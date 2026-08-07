-- Run in Supabase SQL editor if broker_connections already exists without new columns.

alter table public.broker_connections
  add column if not exists public_token_encrypted text,
  add column if not exists kite_user_id text;

-- Create table + RLS if missing entirely:
-- Copy full contents from apex-ui/supabase/schema.sql
