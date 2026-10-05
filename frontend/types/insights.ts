export type InsightItemType = "positive" | "negative" | "neutral" | "suggestion";

export interface InsightItem {
  type: InsightItemType;
  title: string;
  detail: string;
  metric: string;
  badge: string | null;
}

export interface BusinessInsights {
  state: "ready" | "insufficient_data" | "generating" | "unavailable" | "not_configured";
  summary: string | null;
  items: InsightItem[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string | null;
  stale: boolean;
  last_attempt_failed: boolean;
  generating: boolean;
  can_refresh: boolean;
  next_refresh_at: string | null;
  progress: { appointments: number; required: number } | null;
}
