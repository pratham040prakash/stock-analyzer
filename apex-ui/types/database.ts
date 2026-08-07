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
          updated_at: string;
        };
        Insert: {
          user_id: string;
          income_range: string;
          expense_range: string;
          investable_surplus: number;
          updated_at?: string;
        };
        Update: {
          income_range?: string;
          expense_range?: string;
          investable_surplus?: number;
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
