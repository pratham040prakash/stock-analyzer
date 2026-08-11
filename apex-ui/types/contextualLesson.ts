export type ContextualLessonViewModel = {
  built_at: string;
  headline: string;
  lesson: string;
  source: "planned_vs_actual" | "receipt" | "receipt_sequence";
  receipt_id: string | null;
  review_href: string;
};
