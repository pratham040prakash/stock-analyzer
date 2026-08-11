-- Immutable decision receipts for ACT/WAIT and broker fills.
CREATE TABLE IF NOT EXISTS decision_receipts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  receipt_date DATE NOT NULL,
  symbol TEXT NOT NULL,
  execution_kind TEXT NOT NULL CHECK (
    execution_kind IN ('BUY', 'SELL', 'WAIT', 'OBSERVE')
  ),
  verdict_word TEXT,
  headline TEXT,
  subline TEXT,
  trust_score INTEGER,
  trust_delta INTEGER,
  order_id TEXT,
  fill_side TEXT CHECK (fill_side IN ('buy', 'sell')),
  fill_quantity NUMERIC,
  fill_price NUMERIC,
  fill_amount NUMERIC,
  decision_memory_id UUID REFERENCES public.decision_memory (id) ON DELETE SET NULL,
  brief_snapshot JSONB,
  dismissed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS decision_receipts_user_date_symbol_order_idx
  ON decision_receipts (user_id, receipt_date, symbol, COALESCE(order_id, id::text));

ALTER TABLE decision_receipts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS decision_receipts_select_own ON decision_receipts;
CREATE POLICY decision_receipts_select_own ON decision_receipts
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS decision_receipts_insert_own ON decision_receipts;
CREATE POLICY decision_receipts_insert_own ON decision_receipts
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS decision_receipts_update_dismiss ON decision_receipts;
CREATE POLICY decision_receipts_update_dismiss ON decision_receipts
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
