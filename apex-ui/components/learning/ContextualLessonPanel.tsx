"use client";

import Link from "next/link";
import type { ContextualLessonViewModel } from "@/types/contextualLesson";

type Props = {
  lesson: ContextualLessonViewModel | null;
  loading?: boolean;
};

export default function ContextualLessonPanel({ lesson, loading }: Props) {
  if (loading) {
    return null;
  }

  if (!lesson) {
    return null;
  }

  return (
    <section className="rounded-xl border border-purple-500/15 bg-purple-500/5 px-4 py-4 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
        Learning loop
      </p>
      <p className="text-sm font-medium text-apex-text/95">{lesson.headline}</p>
      <p className="text-sm text-apex-muted/85">{lesson.lesson}</p>
      <Link
        href={lesson.review_href}
        className="inline-flex text-sm text-blue-200/90 hover:text-blue-100"
      >
        Open in Review →
      </Link>
    </section>
  );
}
