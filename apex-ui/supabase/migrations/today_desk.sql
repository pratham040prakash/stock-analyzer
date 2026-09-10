-- Night desk: cross-device contract, interrupt dedupe, session tape.
CREATE TABLE IF NOT EXISTS today_contracts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  contract_date DATE NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, contract_date)
);

CREATE TABLE IF NOT EXISTS desk_alerts (
  user_id UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  date_key DATE NOT NULL,
  alert_key TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, date_key, alert_key)
);

ALTER TABLE today_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE desk_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS today_contracts_select_own ON today_contracts;
CREATE POLICY today_contracts_select_own ON today_contracts
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS today_contracts_upsert_own ON today_contracts;
CREATE POLICY today_contracts_upsert_own ON today_contracts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS today_contracts_update_own ON today_contracts;
CREATE POLICY today_contracts_update_own ON today_contracts
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS desk_alerts_select_own ON desk_alerts;
CREATE POLICY desk_alerts_select_own ON desk_alerts
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS desk_alerts_insert_own ON desk_alerts;
CREATE POLICY desk_alerts_insert_own ON desk_alerts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

GRANT SELECT, INSERT, UPDATE ON TABLE public.today_contracts TO authenticated;
GRANT SELECT, INSERT, UPDATE ON TABLE public.today_contracts TO service_role;
GRANT SELECT, INSERT ON TABLE public.desk_alerts TO authenticated;
GRANT SELECT, INSERT ON TABLE public.desk_alerts TO service_role;

NOTIFY pgrst, 'reload schema';
