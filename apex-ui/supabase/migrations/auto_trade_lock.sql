-- Atomic auto-trade lock — one in-flight attempt per user per trading day.
CREATE TABLE IF NOT EXISTS auto_trade_locks (
  user_id UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
  trade_date DATE NOT NULL,
  stock TEXT NOT NULL,
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, trade_date)
);

ALTER TABLE auto_trade_locks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS auto_trade_locks_select_own ON auto_trade_locks;
CREATE POLICY auto_trade_locks_select_own ON auto_trade_locks
  FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS auto_trade_locks_insert_own ON auto_trade_locks;
CREATE POLICY auto_trade_locks_insert_own ON auto_trade_locks
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS auto_trade_locks_delete_own ON auto_trade_locks;
CREATE POLICY auto_trade_locks_delete_own ON auto_trade_locks
  FOR DELETE
  USING (auth.uid() = user_id);
