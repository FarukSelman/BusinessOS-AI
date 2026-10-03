"use client";

import { useEffect, useState } from "react";
import { Clock, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  Branch,
  BusinessHoursItem,
  getBusinessHours,
  resetBranchHours,
  setBusinessHours,
} from "@/lib/api";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

// Backend: 0 = Pazartesi ... 6 = Pazar
const DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"];

// Backend'deki DEFAULT_OPEN_TIME / DEFAULT_CLOSE_TIME ile aynı
const DEFAULT_OPEN = "09:00";
const DEFAULT_CLOSE = "18:00";

interface DayRow {
  day_of_week: number;
  open_time: string;
  close_time: string;
  is_closed: boolean;
}

type Source = "own" | "business" | "default";

const defaultWeek = (): DayRow[] =>
  DAYS.map((_, i) => ({ day_of_week: i, open_time: DEFAULT_OPEN, close_time: DEFAULT_CLOSE, is_closed: false }));

// Kayıtlı bir haftada eksik gün = kapalı (backend ile aynı kural)
const toRows = (items: BusinessHoursItem[]): DayRow[] =>
  DAYS.map((_, i) => {
    const item = items.find((h) => h.day_of_week === i);
    if (!item) return { day_of_week: i, open_time: DEFAULT_OPEN, close_time: DEFAULT_CLOSE, is_closed: true };
    return {
      day_of_week: i,
      open_time: item.open_time?.slice(0, 5) ?? DEFAULT_OPEN,
      close_time: item.close_time?.slice(0, 5) ?? DEFAULT_CLOSE,
      is_closed: item.is_closed,
    };
  });

const withSeconds = (t: string) => (t.length === 5 ? `${t}:00` : t);

// Seçili kapsamın haftasını ve hangi kaynaktan geldiğini getirir.
async function fetchWeek(businessId: string, branchId: string): Promise<{ rows: DayRow[]; source: Source }> {
  if (branchId) {
    const own = await getBusinessHours(businessId, branchId);
    if (own.length > 0) return { rows: toRows(own), source: "own" };
  }
  const business = await getBusinessHours(businessId);
  if (business.length > 0) return { rows: toRows(business), source: branchId ? "business" : "own" };
  return { rows: defaultWeek(), source: "default" };
}

export function BusinessHoursCard({ businessId, branches }: { businessId: string; branches: Branch[] }) {
  const confirmDialog = useConfirm();
  const [branchId, setBranchId] = useState<string>("");
  const [rows, setRows] = useState<DayRow[]>(defaultWeek());
  const [source, setSource] = useState<Source>("default");
  const [saving, setSaving] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  // Yükleniyor durumu, son yüklenen kapsamın seçili kapsamla eşleşip eşleşmediğinden türetilir.
  const scopeKey = `${businessId}:${branchId}:${reloadToken}`;
  const [loadedKey, setLoadedKey] = useState<string | null>(null);
  const loading = loadedKey !== scopeKey;

  useEffect(() => {
    let cancelled = false; // şube hızlı değişirse eski cevap yenisinin üstüne yazmasın
    fetchWeek(businessId, branchId)
      .then(({ rows, source }) => {
        if (cancelled) return;
        setRows(rows);
        setSource(source);
      })
      .catch(() => {
        if (!cancelled) toast.error("Çalışma saatleri yüklenemedi.");
      })
      .finally(() => {
        if (!cancelled) setLoadedKey(scopeKey);
      });
    return () => {
      cancelled = true;
    };
  }, [businessId, branchId, scopeKey]);

  const updateRow = (day: number, patch: Partial<DayRow>) =>
    setRows((prev) => prev.map((r) => (r.day_of_week === day ? { ...r, ...patch } : r)));

  const handleSave = async () => {
    const invalid = rows.find((r) => !r.is_closed && r.open_time >= r.close_time);
    if (invalid) {
      toast.error(`${DAYS[invalid.day_of_week]}: açılış saati kapanıştan önce olmalı.`);
      return;
    }
    setSaving(true);
    try {
      const items: BusinessHoursItem[] = rows.map((r) => ({
        day_of_week: r.day_of_week,
        is_closed: r.is_closed,
        open_time: r.is_closed ? null : withSeconds(r.open_time),
        close_time: r.is_closed ? null : withSeconds(r.close_time),
      }));
      await setBusinessHours(businessId, items, branchId || null);
      toast.success(branchId ? "Şube çalışma saatleri kaydedildi." : "Çalışma saatleri kaydedildi.");
      setSource("own");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Kaydedilirken hata oluştu.");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!branchId) return;
    const ok = await confirmDialog({
      title: "İşletme saatlerine dön",
      description: "Bu şubenin kendi saatleri silinecek ve işletme genel saatleri kullanılacak. Emin misiniz?",
    });
    if (!ok) return;
    try {
      await resetBranchHours(businessId, branchId);
      toast.success("Şube artık işletme genel saatlerini kullanıyor.");
      setReloadToken((t) => t + 1);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Sıfırlanırken hata oluştu.");
    }
  };

  const sourceNote: Record<Source, string> = {
    own: branchId ? "Bu şubenin kendi saatleri gösteriliyor." : "İşletme genel saatleri gösteriliyor.",
    business: "Bu şubenin kendi saati yok, işletme genel saatleri geçerli. Kaydederseniz şubeye özel saat tanımlanır.",
    default: "Henüz saat tanımlanmadı; varsayılan olarak her gün 09:00–18:00 uygulanıyor.",
  };

  return (
    <Card>
      <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-1.5">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4" />
            Haftalık Çalışma Saatleri
          </CardTitle>
          <CardDescription>{loading ? "Yükleniyor..." : sourceNote[source]}</CardDescription>
        </div>
        {branches.length > 0 && (
          <div className="flex flex-col gap-1.5 sm:w-60">
            <Label htmlFor="hours-branch">Kapsam</Label>
            <Select id="hours-branch" value={branchId} onChange={(e) => setBranchId(e.target.value)}>
              <option value="">İşletme geneli</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col divide-y divide-border">
          {rows.map((row) => (
            <div key={row.day_of_week} className="flex flex-wrap items-center gap-3 py-2">
              <span className="w-24 text-sm font-medium text-ink">{DAYS[row.day_of_week]}</span>
              <label className="flex items-center gap-2 text-sm text-ink-muted">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[var(--agent-appointments)]"
                  checked={row.is_closed}
                  disabled={loading}
                  onChange={(e) => updateRow(row.day_of_week, { is_closed: e.target.checked })}
                />
                Kapalı
              </label>
              {row.is_closed ? (
                <span className="text-sm text-ink-muted">Randevu alınmaz</span>
              ) : (
                <div className="flex items-center gap-2">
                  <Input
                    type="time"
                    aria-label={`${DAYS[row.day_of_week]} açılış`}
                    className="w-28"
                    value={row.open_time}
                    disabled={loading}
                    onChange={(e) => updateRow(row.day_of_week, { open_time: e.target.value })}
                  />
                  <span className="text-ink-muted">–</span>
                  <Input
                    type="time"
                    aria-label={`${DAYS[row.day_of_week]} kapanış`}
                    className="w-28"
                    value={row.close_time}
                    disabled={loading}
                    onChange={(e) => updateRow(row.day_of_week, { close_time: e.target.value })}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          {branchId && source === "own" && (
            <Button type="button" variant="outline" className="gap-2" onClick={handleReset}>
              <RotateCcw className="h-4 w-4" />
              İşletme saatlerine dön
            </Button>
          )}
          <Button type="button" onClick={handleSave} disabled={saving || loading}>
            {saving ? "Kaydediliyor..." : "Saatleri kaydet"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
