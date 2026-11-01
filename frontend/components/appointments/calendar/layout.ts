import {
  addDays,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import type { CalendarAppointment } from "@/lib/api";
import { timeToMinutes } from "@/lib/date";

export type CalendarView = "DAY" | "WEEK" | "MONTH";

/** Bitiş saati yoksa hizmet süresi, o da yoksa bu kadar dakika varsayılır. */
export const DEFAULT_DURATION_MIN = 30;
/** Saat ızgarasında 1 dakika = 1 piksel. */
export const PX_PER_MIN = 1;
/** Bir blok bundan kısa çizilmez (tek satır metin sığsın). */
export const MIN_BLOCK_MIN = 22;

const WEEK_OPTS = { weekStartsOn: 1 } as const; // Pazartesi

/** Görünümün kapsadığı günler (ay görünümünde 6 haftaya kadar tam haftalar). */
export function visibleDays(view: CalendarView, anchor: Date): Date[] {
  if (view === "DAY") return [anchor];
  if (view === "WEEK") {
    return eachDayOfInterval({ start: startOfWeek(anchor, WEEK_OPTS), end: endOfWeek(anchor, WEEK_OPTS) });
  }
  return eachDayOfInterval({
    start: startOfWeek(startOfMonth(anchor), WEEK_OPTS),
    end: endOfWeek(endOfMonth(anchor), WEEK_OPTS),
  });
}

export function stepAnchor(view: CalendarView, anchor: Date, dir: 1 | -1): Date {
  if (view === "DAY") return addDays(anchor, dir);
  if (view === "WEEK") return addDays(anchor, 7 * dir);
  return new Date(anchor.getFullYear(), anchor.getMonth() + dir, 1);
}

export interface TimedAppointment {
  appt: CalendarAppointment;
  start: number; // gün başından dakika
  end: number;
}

export function toTimed(appt: CalendarAppointment, durationOf: (serviceId: string | null) => number | null): TimedAppointment {
  const start = timeToMinutes(appt.start_time);
  let end = appt.end_time ? timeToMinutes(appt.end_time) : start + (durationOf(appt.service_id) ?? DEFAULT_DURATION_MIN);
  if (end <= start) end = start + DEFAULT_DURATION_MIN;
  return { appt, start, end };
}

export interface PositionedBlock {
  kind: "appt";
  item: TimedAppointment;
  column: number;
  columns: number;
}

export interface OverflowBlock {
  kind: "overflow";
  hidden: TimedAppointment[];
  start: number;
  end: number;
  column: number;
  columns: number;
}

/**
 * Çakışan randevuları yan yana sütunlara dağıtır. Bir çakışma grubu
 * maxColumns'tan fazla sütun gerektirirse son sütun "+N" kutusuna dönüşür.
 */
export function layoutDay(items: TimedAppointment[], maxColumns = Infinity): (PositionedBlock | OverflowBlock)[] {
  const sorted = [...items].sort((a, b) => a.start - b.start || b.end - a.end);
  const out: (PositionedBlock | OverflowBlock)[] = [];

  let cluster: TimedAppointment[] = [];
  let clusterEnd = -1;

  const flush = () => {
    if (cluster.length === 0) return;
    const columnEnds: number[] = [];
    const placed = cluster.map((item) => {
      const visualEnd = Math.max(item.end, item.start + MIN_BLOCK_MIN);
      let col = columnEnds.findIndex((end) => end <= item.start);
      if (col === -1) {
        col = columnEnds.length;
        columnEnds.push(visualEnd);
      } else {
        columnEnds[col] = visualEnd;
      }
      return { item, col };
    });

    const columns = columnEnds.length;
    if (columns <= maxColumns) {
      for (const p of placed) out.push({ kind: "appt", item: p.item, column: p.col, columns });
    } else {
      const keep = maxColumns - 1;
      const hidden = placed.filter((p) => p.col >= keep).map((p) => p.item);
      for (const p of placed) {
        if (p.col < keep) out.push({ kind: "appt", item: p.item, column: p.col, columns: maxColumns });
      }
      out.push({
        kind: "overflow",
        hidden,
        start: Math.min(...hidden.map((h) => h.start)),
        end: Math.max(...hidden.map((h) => Math.max(h.end, h.start + MIN_BLOCK_MIN))),
        column: keep,
        columns: maxColumns,
      });
    }
    cluster = [];
    clusterEnd = -1;
  };

  for (const item of sorted) {
    if (cluster.length > 0 && item.start >= clusterEnd) flush();
    cluster.push(item);
    clusterEnd = Math.max(clusterEnd, item.end, item.start + MIN_BLOCK_MIN);
  }
  flush();
  return out;
}
