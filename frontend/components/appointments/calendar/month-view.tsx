"use client";

import { memo } from "react";
import { isSameMonth } from "date-fns";
import type { CalendarAppointment } from "@/lib/api";
import { toISODate, todayISO } from "@/lib/date";
import { cn } from "@/lib/utils";
import { statusStyles } from "../constants";
import { AppointmentBlock } from "./appointment-block";

const WEEKDAYS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"];
const MAX_VISIBLE = 3;

interface Props {
  days: Date[];
  anchor: Date;
  byDate: Map<string, CalendarAppointment[]>;
  staffColor: (id: string | null) => string | null;
  serviceName: (id: string | null) => string | null;
  /** Dar ekranda satır yerine nokta + sayı gösterilir. */
  narrow: boolean;
  onSelectAppointment: (id: string) => void;
  onOpenDay: (date: string) => void;
}

function MonthViewImpl({ days, anchor, byDate, staffColor, serviceName, narrow, onSelectAppointment, onOpenDay }: Props) {
  const today = todayISO();

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="grid grid-cols-7 border-b border-border bg-surface-elevated">
        {WEEKDAYS.map((d) => (
          <div key={d} className="py-2 text-center text-xs font-semibold text-ink-muted">
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-px bg-border">
        {days.map((day) => {
          const iso = toISODate(day);
          const appts = byDate.get(iso) ?? [];
          const inMonth = isSameMonth(day, anchor);
          return (
            <div
              key={iso}
              role="button"
              tabIndex={0}
              aria-label={`${iso}, ${appts.length} randevu`}
              onClick={() => onOpenDay(iso)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onOpenDay(iso);
                }
              }}
              className={cn(
                "flex cursor-pointer flex-col gap-1 p-1 outline-none transition-colors hover:bg-surface focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent sm:p-1.5",
                narrow ? "min-h-[64px]" : "min-h-[108px]",
                inMonth ? "bg-surface-elevated" : "bg-surface/70"
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium tabular-nums",
                  iso === today ? "bg-accent text-white" : inMonth ? "text-ink" : "text-ink-muted/60"
                )}
              >
                {day.getDate()}
              </span>

              {narrow ? (
                appts.length > 0 && (
                  <div className="flex flex-wrap items-center gap-0.5">
                    {appts.slice(0, 4).map((a) => (
                      <span
                        key={a.id}
                        className="h-1.5 w-1.5 rounded-full"
                        style={{ backgroundColor: statusStyles[a.status].color }}
                      />
                    ))}
                    <span className="text-[10px] font-medium tabular-nums text-ink-muted">{appts.length}</span>
                  </div>
                )
              ) : (
                <>
                  {appts.slice(0, MAX_VISIBLE).map((a) => (
                    <AppointmentBlock
                      key={a.id}
                      appt={a}
                      staffColor={staffColor(a.staff_id)}
                      serviceName={serviceName(a.service_id)}
                      compact
                      onSelect={onSelectAppointment}
                    />
                  ))}
                  {appts.length > MAX_VISIBLE && (
                    <span className="px-1 text-[10px] font-medium text-ink-muted">
                      +{appts.length - MAX_VISIBLE} daha
                    </span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export const MonthView = memo(MonthViewImpl);
