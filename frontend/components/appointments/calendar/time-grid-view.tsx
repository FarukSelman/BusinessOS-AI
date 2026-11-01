"use client";

import { memo, useEffect, useMemo, useRef, useState } from "react";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import type { CalendarAppointment } from "@/lib/api";
import { minutesToHm, toISODate, todayISO } from "@/lib/date";
import { cn } from "@/lib/utils";
import { AppointmentBlock } from "./appointment-block";
import { MIN_BLOCK_MIN, PX_PER_MIN, layoutDay, toTimed } from "./layout";

const SLOT_SNAP_MIN = 15;

interface Props {
  days: Date[];
  byDate: Map<string, CalendarAppointment[]>;
  /** Izgaranın kapsadığı aralık, gün başından dakika (tam saatlere yuvarlı). */
  startMin: number;
  endMin: number;
  staffColor: (id: string | null) => string | null;
  serviceName: (id: string | null) => string | null;
  durationOf: (serviceId: string | null) => number | null;
  /** Çakışma grubunda en fazla bu kadar sütun; fazlası "+N" olur. */
  maxColumns: number;
  onSelectAppointment: (id: string) => void;
  onSlotClick: (date: string, time: string) => void;
  onOpenDay?: (date: string) => void;
}

function useNowMinutes() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);
  return { today: toISODate(now), minutes: now.getHours() * 60 + now.getMinutes() };
}

function TimeGridViewImpl({
  days,
  byDate,
  startMin,
  endMin,
  staffColor,
  serviceName,
  durationOf,
  maxColumns,
  onSelectAppointment,
  onSlotClick,
  onOpenDay,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const now = useNowMinutes();
  const height = (endMin - startMin) * PX_PER_MIN;
  const isWeek = days.length > 1;
  const today = todayISO();

  const hours = useMemo(() => {
    const out: number[] = [];
    for (let m = startMin; m < endMin; m += 60) out.push(m);
    return out;
  }, [startMin, endMin]);

  const columns = useMemo(
    () =>
      days.map((day) => {
        const iso = toISODate(day);
        const timed = (byDate.get(iso) ?? []).map((a) => toTimed(a, durationOf));
        return { day, iso, blocks: layoutDay(timed, maxColumns) };
      }),
    [days, byDate, durationOf, maxColumns]
  );

  // Bugün görünüyorsa ilk açılışta şimdiki saatin biraz öncesine kaydır.
  const showsToday = columns.some((c) => c.iso === today);
  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !showsToday) return;
    el.scrollTop = Math.max(0, (now.minutes - startMin - 60) * PX_PER_MIN);
    // sadece görünüm/aralık değişince
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showsToday, startMin]);

  function handleColumnClick(e: React.MouseEvent<HTMLDivElement>, iso: string) {
    const rect = e.currentTarget.getBoundingClientRect();
    const offset = (e.clientY - rect.top) / PX_PER_MIN;
    const minutes = startMin + Math.floor(offset / SLOT_SNAP_MIN) * SLOT_SNAP_MIN;
    onSlotClick(iso, minutesToHm(minutes));
  }

  return (
    <div
      ref={scrollRef}
      className="max-h-[calc(100vh-15rem)] min-h-[360px] overflow-auto rounded-lg border border-border bg-surface-elevated"
    >
      <div className={cn("relative", isWeek && "min-w-[760px]")}>
        {/* Gün başlıkları */}
        <div className="sticky top-0 z-20 flex border-b border-border bg-surface-elevated">
          <div className="sticky left-0 z-10 w-12 shrink-0 bg-surface-elevated" />
          {columns.map(({ day, iso, blocks }) => {
            const count = blocks.reduce((n, b) => n + (b.kind === "appt" ? 1 : b.hidden.length), 0);
            const label = (
              <>
                <span className="text-[11px] uppercase text-ink-muted">{format(day, "EEE", { locale: tr })}</span>
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold tabular-nums",
                    iso === today ? "bg-accent text-white" : "text-ink"
                  )}
                >
                  {day.getDate()}
                </span>
                {count > 0 && <span className="text-[10px] tabular-nums text-ink-muted">{count} randevu</span>}
              </>
            );
            return isWeek && onOpenDay ? (
              <button
                key={iso}
                type="button"
                onClick={() => onOpenDay(iso)}
                className="flex flex-1 flex-col items-center gap-0.5 border-l border-border py-1.5 hover:bg-surface"
              >
                {label}
              </button>
            ) : (
              <div key={iso} className="flex flex-1 flex-col items-center gap-0.5 border-l border-border py-1.5">
                {label}
              </div>
            );
          })}
        </div>

        <div className="flex">
          {/* Saat sütunu */}
          <div className="sticky left-0 z-10 w-12 shrink-0 border-r border-border bg-surface-elevated" style={{ height }}>
            {hours.map((m) => (
              <div
                key={m}
                className="absolute right-1.5 -translate-y-1/2 text-[10px] tabular-nums text-ink-muted first:translate-y-0"
                style={{ top: (m - startMin) * PX_PER_MIN }}
              >
                {minutesToHm(m)}
              </div>
            ))}
          </div>

          {columns.map(({ iso, blocks }) => (
            <div
              key={iso}
              onClick={(e) => handleColumnClick(e, iso)}
              className={cn("relative flex-1 cursor-cell border-l border-border", iso === today && "bg-accent/[0.03]")}
              style={{
                height,
                backgroundImage:
                  "linear-gradient(to bottom, var(--border) 1px, transparent 1px), linear-gradient(to bottom, color-mix(in srgb, var(--border) 45%, transparent) 1px, transparent 1px)",
                backgroundSize: `100% ${60 * PX_PER_MIN}px, 100% ${30 * PX_PER_MIN}px`,
              }}
            >
              {blocks.map((b) => {
                const start = b.kind === "appt" ? b.item.start : b.start;
                const end = b.kind === "appt" ? Math.max(b.item.end, b.item.start + MIN_BLOCK_MIN) : b.end;
                const top = (Math.max(start, startMin) - startMin) * PX_PER_MIN;
                const h = Math.max((Math.min(end, endMin) - Math.max(start, startMin)) * PX_PER_MIN - 1, MIN_BLOCK_MIN);
                const style: React.CSSProperties = {
                  top,
                  height: h,
                  left: `calc(${(b.column / b.columns) * 100}% + 2px)`,
                  width: `calc(${100 / b.columns}% - 4px)`,
                };
                if (b.kind === "overflow") {
                  return (
                    <button
                      key={`more-${b.hidden[0].appt.id}`}
                      type="button"
                      title={`${b.hidden.length} randevu daha`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenDay?.(iso);
                      }}
                      className="absolute z-[1] flex items-start justify-center rounded-[4px] bg-ink/10 pt-0.5 text-[11px] font-semibold text-ink hover:bg-ink/15"
                      style={style}
                    >
                      +{b.hidden.length}
                    </button>
                  );
                }
                const a = b.item.appt;
                return (
                  <AppointmentBlock
                    key={a.id}
                    appt={a}
                    staffColor={staffColor(a.staff_id)}
                    serviceName={serviceName(a.service_id)}
                    style={{ ...style, zIndex: 1 }}
                    roomy={h >= 40}
                    onSelect={onSelectAppointment}
                  />
                );
              })}

              {iso === now.today && now.minutes >= startMin && now.minutes <= endMin && (
                <div
                  className="pointer-events-none absolute inset-x-0 z-[2] h-px bg-danger"
                  style={{ top: (now.minutes - startMin) * PX_PER_MIN }}
                >
                  <span className="absolute -left-1 -top-1 h-2 w-2 rounded-full bg-danger" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export const TimeGridView = memo(TimeGridViewImpl);
