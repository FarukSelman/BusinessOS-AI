"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, getInsights, refreshInsights } from "@/lib/api";
import type { BusinessInsights, InsightItemType } from "@/types/insights";

const POLL_MS = 4000;
const POLL_LIMIT_MS = 90_000;

const TYPE_STYLE: Record<InsightItemType, { emoji: string; label: string; badge: string }> = {
  positive: { emoji: "🟢", label: "Olumlu", badge: "bg-green-500/10 text-green-700 dark:text-green-400" },
  negative: { emoji: "🔴", label: "Olumsuz", badge: "bg-red-500/10 text-red-700 dark:text-red-400" },
  neutral: { emoji: "⚪", label: "Nötr", badge: "bg-ink-muted/10 text-ink-muted" },
  suggestion: { emoji: "💡", label: "Öneri", badge: "bg-amber-500/10 text-amber-700 dark:text-amber-400" },
};

function formatWhen(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("tr-TR", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });
}

function minutesUntil(iso: string | null) {
  if (!iso) return 0;
  return Math.max(1, Math.ceil((new Date(iso).getTime() - Date.now()) / 60000));
}

interface Props {
  businessId: string | null;
  /** Rule-based lines from the old "Günlük özet" card, shown when there is no AI insight. */
  fallback: React.ReactNode;
}

/**
 * Dashboard "AI İçgörüleri". Loads independently of the rest of the dashboard:
 * any error here only changes this card. Roles without access (403) see the
 * plain daily summary instead.
 */
export function AiInsightsCard({ businessId, fallback }: Props) {
  const [data, setData] = useState<BusinessInsights | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [failed, setFailed] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const pollStarted = useRef<number | null>(null);

  const load = useCallback(async () => {
    if (!businessId) return;
    try {
      const result = await getInsights(businessId);
      setData(result);
      setFailed(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) setForbidden(true);
      else setFailed(true);
    }
  }, [businessId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial load from the API
    load();
  }, [load]);

  // While a generation runs, poll until it finishes (bounded).
  useEffect(() => {
    if (!data?.generating) {
      pollStarted.current = null;
      return;
    }
    pollStarted.current ??= Date.now();
    if (Date.now() - pollStarted.current > POLL_LIMIT_MS) return;
    const timer = setTimeout(load, POLL_MS);
    return () => clearTimeout(timer);
  }, [data, load]);

  async function handleRefresh() {
    if (!businessId) return;
    setRefreshing(true);
    try {
      setData(await refreshInsights(businessId));
      pollStarted.current = Date.now();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İçgörüler yenilenemedi.");
    } finally {
      setRefreshing(false);
    }
  }

  if (forbidden) {
    return (
      <Card className="border-l-4 border-l-[var(--agent-marketing)]">
        <CardHeader className="flex-row items-start gap-3 space-y-0 pb-3">
          <Sparkles className="mt-0.5 h-5 w-5 text-[var(--agent-marketing)]" />
          <div>
            <CardTitle className="text-base">Günlük özet</CardTitle>
            <CardDescription>Bugünün verilerine göre</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-2 pt-0 text-sm text-ink-muted sm:grid-cols-2">{fallback}</CardContent>
      </Card>
    );
  }

  const state = failed ? "unavailable" : data?.state;
  const items = data?.items ?? [];
  const findings = items.filter((i) => i.type !== "suggestion");
  const suggestion = items.find((i) => i.type === "suggestion");

  return (
    <Card className="border-l-4 border-l-[var(--agent-marketing)] bg-gradient-to-r from-[color-mix(in_srgb,var(--agent-marketing)_10%,transparent)] to-surface">
      <CardHeader className="flex-row items-start gap-3 space-y-0 pb-3">
        <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-[var(--agent-marketing)]" />
        <div className="min-w-0 flex-1">
          <CardTitle className="text-base">AI İçgörüleri</CardTitle>
          <CardDescription>
            {data?.generated_at
              ? `Son 30 gün, önceki 30 günle karşılaştırma · ${data.stale ? "Önceki günden" : "Bugün"} ${formatWhen(data.generated_at)}`
              : "Son 30 gün, önceki 30 günle karşılaştırma"}
          </CardDescription>
        </div>
        {data && state !== "not_configured" && (
          <button
            type="button"
            onClick={handleRefresh}
            disabled={!data.can_refresh || refreshing || data.generating}
            title={
              data.generating
                ? "İçgörüler hazırlanıyor"
                : data.next_refresh_at
                  ? `Saatte bir yenilenebilir · yaklaşık ${minutesUntil(data.next_refresh_at)} dk sonra`
                  : "İçgörüleri yeniden üret"
            }
            className="flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-xs text-ink-muted transition-colors hover:bg-surface hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${data.generating || refreshing ? "animate-spin" : ""}`} />
            Yenile
          </button>
        )}
      </CardHeader>

      <CardContent className="pt-0 text-sm">
        {!data && !failed && (
          <div className="space-y-2" aria-busy="true">
            <div className="h-4 w-2/3 animate-pulse rounded bg-ink-muted/15" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-ink-muted/15" />
          </div>
        )}

        {data?.generating && items.length === 0 && (
          <p className="flex items-center gap-2 text-ink-muted">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" /> İçgörüler hazırlanıyor, birkaç saniye sürebilir…
          </p>
        )}

        {state === "ready" || (data?.generating && items.length > 0) ? (
          <div className="flex flex-col gap-3">
            {data?.summary && <p className="font-medium text-ink">{data.summary}</p>}
            <ul className="grid gap-2 md:grid-cols-2">
              {findings.map((item, i) => (
                <li key={i} className="rounded-lg border border-border bg-surface/60 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-ink">
                      <span className="mr-1.5" aria-label={TYPE_STYLE[item.type].label}>{TYPE_STYLE[item.type].emoji}</span>
                      {item.title}
                    </p>
                    {item.badge && (
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${TYPE_STYLE[item.type].badge}`}>
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-ink-muted">{item.detail}</p>
                </li>
              ))}
            </ul>
            {suggestion && (
              <div className="rounded-lg border border-amber-400/40 bg-amber-50/60 p-3 dark:bg-amber-500/5">
                <p className="font-medium text-ink">
                  <span className="mr-1.5" aria-label="Öneri">💡</span>
                  {suggestion.title}
                  {suggestion.badge && (
                    <span className="ml-2 rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-700 dark:text-amber-400">
                      {suggestion.badge}
                    </span>
                  )}
                </p>
                <p className="mt-1 text-ink-muted">{suggestion.detail}</p>
              </div>
            )}
            {(data?.stale || data?.last_attempt_failed) && (
              <p className="text-[11px] text-ink-muted">
                {data.last_attempt_failed
                  ? "Son güncelleme denemesi başarısız oldu; önceki içgörüler gösteriliyor."
                  : "Bugünün içgörüleri henüz hazır değil; önceki içgörüler gösteriliyor."}
              </p>
            )}
          </div>
        ) : null}

        {state === "insufficient_data" && !data?.generating && (
          <div className="flex flex-col gap-3">
            <div>
              <p className="font-medium text-ink">Henüz yeterli veri yok</p>
              <p className="text-ink-muted">
                Anlamlı içgörüler için son 60 günde en az {data?.progress?.required ?? 5} randevu ya da ödenmiş bir fatura gerekiyor.
              </p>
              {data?.progress && (
                <div className="mt-2 flex items-center gap-2 text-xs text-ink-muted">
                  <div className="h-1.5 w-40 overflow-hidden rounded-full bg-ink-muted/15">
                    <div
                      className="h-full rounded-full bg-[var(--agent-marketing)]"
                      style={{ width: `${Math.min(100, (data.progress.appointments / Math.max(1, data.progress.required)) * 100)}%` }}
                    />
                  </div>
                  {Math.min(data.progress.appointments, data.progress.required)} / {data.progress.required} randevu
                </div>
              )}
            </div>
            <div className="grid gap-2 text-ink-muted sm:grid-cols-2">{fallback}</div>
          </div>
        )}

        {(state === "unavailable" || state === "not_configured") && !data?.generating && (
          <div className="flex flex-col gap-3">
            <p className="text-ink-muted">
              {state === "not_configured"
                ? "AI içgörüleri için OpenAI anahtarı tanımlı değil."
                : "İçgörü şu an hazır değil. Biraz sonra tekrar deneyebilirsin."}
            </p>
            <div className="grid gap-2 text-ink-muted sm:grid-cols-2">{fallback}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
