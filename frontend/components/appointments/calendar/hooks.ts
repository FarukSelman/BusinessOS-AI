"use client";

import { useEffect, useState } from "react";
import { ApiError, listAppointmentsInRange, type CalendarAppointment } from "@/lib/api";

const CACHE_LIMIT = 12;

interface RangeStore {
  refreshKey: number;
  entries: [string, CalendarAppointment[]][];
  error: { key: string; message: string } | null;
}

/**
 * Görünen aralığın randevularını çeker. Aynı aralığa geri dönülünce önbellekten
 * verir; aralık/filtre değişince önceki istek iptal edilir. refreshKey değişince
 * yeniden çekilir, yeni veri gelene kadar eldeki veri gösterilmeye devam eder.
 */
export function useCalendarRange(
  businessId: string | null,
  start: string,
  end: string,
  staffId: string | null,
  branchId: string | null,
  refreshKey: number
) {
  const key = `${start}|${end}|${staffId ?? ""}|${branchId ?? ""}`;
  const [store, setStore] = useState<RangeStore>({ refreshKey, entries: [], error: null });

  const entry = store.entries.find(([k]) => k === key)?.[1];
  const fresh = entry !== undefined && store.refreshKey === refreshKey;
  const error = store.error?.key === key ? store.error.message : null;

  useEffect(() => {
    if (!businessId || fresh) return;
    const controller = new AbortController();
    listAppointmentsInRange(businessId, start, end, { staffId, branchId }, controller.signal)
      .then((data) =>
        setStore((prev) => {
          const kept = prev.refreshKey === refreshKey ? prev.entries.filter(([k]) => k !== key) : [];
          return { refreshKey, entries: [...kept, [key, data] as [string, CalendarAppointment[]]].slice(-CACHE_LIMIT), error: null };
        })
      )
      .catch((err) => {
        if (controller.signal.aborted) return;
        const message = err instanceof ApiError ? err.message : "Takvim yüklenemedi.";
        setStore((prev) => ({ ...prev, error: { key, message } }));
      });
    return () => controller.abort();
  }, [businessId, key, start, end, staffId, branchId, refreshKey, fresh]);

  return { data: entry ?? [], loading: !fresh && !error, error };
}

/** localStorage'da hatırlanan değer; okunamazsa/yazılamazsa sessizce varsayılana düşer. */
export function usePersistentState<T>(storageKey: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return initial;
    try {
      const raw = window.localStorage.getItem(storageKey);
      return raw ? { ...initial, ...JSON.parse(raw) } : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      // gizli pencere / kota dolu: tercih sadece bu oturumda kalır
    }
  }, [storageKey, value]);

  return [value, setValue] as const;
}

/** Ekran 768px'in altında mı (Tailwind md kırılımı). */
export function useIsNarrow() {
  const [narrow, setNarrow] = useState(() =>
    typeof window === "undefined" ? false : window.matchMedia("(max-width: 767px)").matches
  );
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 767px)");
    const onChange = () => setNarrow(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return narrow;
}
