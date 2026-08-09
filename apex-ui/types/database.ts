import type { SupabaseClient } from "@supabase/supabase-js";
import type { Portfolio } from "@/types/portfolio";
import type { MentorDecision } from "@/types/mentorDecision";
import type { FinancialProfile } from "@/lib/financialProfile";
import type { DailyDecisionType } from "@/types/decision";

export type Database = {
  public: {
    Tables: {
      broker_connections: {
        Row: {
          id: string;
          user_id: string;
          broker: string;
          access_token: string | null;
          access_token_encrypted: string | null;
          public_token: string | null;
          public_token_encrypted: string | null;
          kite_user_id: string | null;
          status: "active" | "expired" | "revoked";
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          broker?: string;
          access_token?: string | null;
          access_token_encrypted?: string | null;
          public_token?: string | null;
          public_token_encrypted?: string | null;
          kite_user_id?: string | null;
          status?: "active" | "expired" | "revoked";
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          access_token?: string | null;
          access_token_encrypted?: string | null;
          public_token?: string | null;
          public_token_encrypted?: string | null;
          kite_user_id?: string | null;
          status?: "active" | "expired" | "revoked";
          updated_at?: string;
        };
        Relationships: [];
      };
      portfolio_snapshots: {
        Row: {
          id: string;
          user_id: string;
          holdings: Portfolio["holdings"];
          total_value: number;
          pnl: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          holdings: Portfolio["holdings"];
          total_value: number;
          pnl: number;
          created_at?: string;
        };
        Update: {
          holdings?: Portfolio["holdings"];
          total_value?: number;
          pnl?: number;
        };
        Relationships: [];
      };
      financial_profiles: {
        Row: {
          user_id: string;
          income_range: string;
          expense_range: string;
          investable_surplus: number;
          auto_trading_enabled: boolean;
          updated_at: string;
        };
        Insert: {
          user_id: string;
          income_range: string;
          expense_range: string;
          investable_surplus: number;
          auto_trading_enabled?: boolean;
          updated_at?: string;
        };
        Update: {
          income_range?: string;
          expense_range?: string;
          investable_surplus?: number;
          auto_trading_enabled?: boolean;
          updated_at?: string;
        };
        Relationships: [];
      };
      mentor_outputs: {
        Row: {
          id: string;
          user_id: string;
          decision: MentorDecision;
          message: string;
          confidence: "low" | "medium" | "high";
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          decision: MentorDecision;
          message: string;
          confidence: "low" | "medium" | "high";
          created_at?: string;
        };
        Update: {
          decision?: MentorDecision;
          message?: string;
          confidence?: "low" | "medium" | "high";
        };
        Relationships: [];
      };
      decisions: {
        Row: {
          id: string;
          user_id: string;
          decision_date: string;
          decision: DailyDecisionType;
          action: string;
          stock: string | null;
          confidence: number;
          reason: string;
          actions: string[];
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          decision_date?: string;
          decision: DailyDecisionType;
          action?: string;
          stock?: string | null;
          confidence: number;
          reason: string;
          actions?: string[];
          created_at?: string;
        };
        Update: {
          decision_date?: string;
          decision?: DailyDecisionType;
          action?: string;
          stock?: string | null;
          confidence?: number;
          reason?: string;
          actions?: string[];
        };
        Relationships: [];
      };
      decision_memory: {
        Row: {
          id: string;
          user_id: string;
          timestamp_ms: number;
          decision_date: string;
          intent: string | null;
          stock: string | null;
          action: string;
          amount: number | null;
          confidence: number;
          signals: import("@/types/decision").Signals | null;
          market_trend: string | null;
          portfolio_snapshot: import("@/types/decision").PortfolioSnapshotInput | null;
          entry_price: number | null;
          exit_price: number | null;
          stop_loss: number | null;
          quantity: number | null;
          take_profit_taken: boolean;
          pnl: number | null;
          success: boolean | null;
          trust_evaluated_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          timestamp_ms: number;
          decision_date?: string;
          intent?: string | null;
          stock?: string | null;
          action: string;
          amount?: number | null;
          confidence: number;
          signals?: import("@/types/decision").Signals | null;
          market_trend?: string | null;
          portfolio_snapshot?: import("@/types/decision").PortfolioSnapshotInput | null;
          entry_price?: number | null;
          exit_price?: number | null;
          stop_loss?: number | null;
          quantity?: number | null;
          take_profit_taken?: boolean;
          pnl?: number | null;
          success?: boolean | null;
          trust_evaluated_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          decision_date?: string;
          intent?: string | null;
          stock?: string | null;
          action?: string;
          amount?: number | null;
          confidence?: number;
          signals?: import("@/types/decision").Signals | null;
          market_trend?: string | null;
          portfolio_snapshot?: import("@/types/decision").PortfolioSnapshotInput | null;
          entry_price?: number | null;
          exit_price?: number | null;
          stop_loss?: number | null;
          quantity?: number | null;
          take_profit_taken?: boolean;
          pnl?: number | null;
          success?: boolean | null;
          trust_evaluated_at?: string | null;
          updated_at?: string;
        };
        Relationships: [];
      };
      discipline_streak_state: {
        Row: {
          user_id: string;
          streak_count: number;
          last_commit_date: string | null;
          last_decision_key: string | null;
          last_action_followed: boolean;
          updated_at: string;
        };
        Insert: {
          user_id: string;
          streak_count?: number;
          last_commit_date?: string | null;
          last_decision_key?: string | null;
          last_action_followed?: boolean;
          updated_at?: string;
        };
        Update: {
          streak_count?: number;
          last_commit_date?: string | null;
          last_decision_key?: string | null;
          last_action_followed?: boolean;
          updated_at?: string;
        };
        Relationships: [];
      };
      discipline_commits: {
        Row: {
          id: string;
          user_id: string;
          commit_date: string;
          intent: string;
          action: string;
          stock: string | null;
          decision_key: string;
          followed: boolean;
          streak_count: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          commit_date: string;
          intent: string;
          action: string;
          stock?: string | null;
          decision_key: string;
          followed?: boolean;
          streak_count?: number;
          created_at?: string;
        };
        Update: {
          commit_date?: string;
          intent?: string;
          action?: string;
          stock?: string | null;
          decision_key?: string;
          followed?: boolean;
          streak_count?: number;
        };
        Relationships: [];
      };
      user_trust_state: {
        Row: {
          user_id: string;
          trust_score: number;
          last_trust_delta: number;
          last_outcome: import("@/services/learning/outcomeEngine").OutcomeEvaluationOutput | null;
          last_decision_id: string | null;
          last_closed_at: string | null;
          last_stock: string | null;
          updated_at: string;
        };
        Insert: {
          user_id: string;
          trust_score?: number;
          last_trust_delta?: number;
          last_outcome?: import("@/services/learning/outcomeEngine").OutcomeEvaluationOutput | null;
          last_decision_id?: string | null;
          last_closed_at?: string | null;
          last_stock?: string | null;
          updated_at?: string;
        };
        Update: {
          trust_score?: number;
          last_trust_delta?: number;
          last_outcome?: import("@/services/learning/outcomeEngine").OutcomeEvaluationOutput | null;
          last_decision_id?: string | null;
          last_closed_at?: string | null;
          last_stock?: string | null;
          updated_at?: string;
        };
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
};

export type AppSupabaseClient = SupabaseClient<Database>;

export type DbFinancialProfile = {
  user_id: string;
  income_range: FinancialProfile["incomeRange"];
  expense_range: FinancialProfile["expenseRange"];
  investable_surplus: number;
  updated_at: string;
};
