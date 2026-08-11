-- Per-symbol investment thesis + invalidation rules (Phase 4 foundation).
CREATE TABLE IF NOT EXISTS investment_thesis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  thesis TEXT NOT NULL,
  invalidation TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, symbol)
);

ALTER TABLE investment_thesis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS investment_thesis_select_own ON investment_thesis;
CREATE POLICY investment_thesis_select_own ON investment_thesis
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS investment_thesis_insert_own ON investment_thesis;
CREATE POLICY investment_thesis_insert_own ON investment_thesis
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS investment_thesis_update_own ON investment_thesis;
CREATE POLICY investment_thesis_update_own ON investment_thesis
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS investment_thesis_delete_own ON investment_thesis;
CREATE POLICY investment_thesis_delete_own ON investment_thesis
  FOR DELETE
  USING (auth.uid() = user_id);
