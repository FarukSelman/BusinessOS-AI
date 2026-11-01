"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import {
  getBusinessHours,
  type BusinessHours,
  type Branch,
  type BusinessService,
  type CalendarAppointment,
  type StaffProfile,
} from "@/lib/api";
import { fromISODate, timeToMinutes, toISODate, todayISO } from "@/lib/date";
import { CalendarToolbar } from "./calendar-toolbar";
import { useCalendarRange, useIsNarrow, usePersistentState } from "./hooks";
import { stepAnchor, toTimed, visibleDays, type CalendarView } from "./layout";
import { MonthView } from "./month-view";
import { TimeGridView } from "./time-grid-view";

const FALLBACK_START = 8 * 60;
const FALLBACK_END = 20 * 60;
/** Personel filtresi yokken haftalık görünümde bir saatte en fazla bu kadar sütun. */
const WEEK_MAX_COLUMNS = 3;

interface Prefs {
  staffId: string | null;
  branchId: string | null;
  hideCancelled: boolean;
}

const DEFAULT_PREFS: Prefs = { staffId: null, branchId: null, hideCancelled: true };

interface Props {
  businessId: string;
  /** Takvimin odak günü (YYYY-MM-DD); liste görünümüyle ortak. */
  date: string;
  onDateChange: (date: string) => void;
  services: BusinessService[];
  staff: StaffProfile[];
  branches: Branch[];
  /** Bir randevu değişince artırılır; takvim önbelleği boşaltılıp yeniden çekilir. */
  refreshKey: number;
  onSelectAppointment: (id: string) => void;
  onSlotClick: (date: string, time: string) => void;
}

function rangeTitle(view: CalendarView, days: Date[], anchor: Date) {
  if (view === "DAY") return format(anchor, "d MMMM yyyy, EEEE", { locale: tr });
  if (view === "MONTH") return format(anchor, "LLLL yyyy", { locale: tr });
  const first = days[0];
  const last = days[days.length - 1];
  const sameMonth = first.getMonth() === last.getMonth();
  return `${format(first, sameMonth ? "d" : "d MMM", { locale: tr })} – ${format(last, "d MMM yyyy", { locale: tr })}`;
}

export function AppointmentCalendar({
  businessId,
  date,
  onDateChange,
  services,
  staff,
  branches,
  refreshKey,
  onSelectAppointment,
  onSlotClick,
}: Props) {
  const narrow = useIsNarrow();
  const [view, setView] = useState<CalendarView>(() => (narrow ? "DAY" : "WEEK"));
  const [prefs, setPrefs] = usePersistentState<Prefs>(`appointments-calendar:${businessId}`, DEFAULT_PREFS);
  const [hours, setHours] = useState<BusinessHours[]>([]);

  // Hatırlanan şube/personel silinmiş olabilir: listelerde yoksa filtre uygulanmaz.
  const branchId = prefs.branchId && branches.some((b) => b.id === prefs.branchId) ? prefs.branchId : null;
  const staffInBranch = useMemo(
    () => (branchId ? staff.filter((s) => s.branch_id === branchId || s.branch_id === null) : staff),
    [staff, branchId]
  );
  const staffId = prefs.staffId && staffInBranch.some((s) => s.id === prefs.staffId) ? prefs.staffId : null;

  const anchor = useMemo(() => fromISODate(date), [date]);
  const days = useMemo(() => visibleDays(view, anchor), [view, anchor]);
  const start = toISODate(days[0]);
  const end = toISODate(days[days.length - 1]);

  const { data, loading, error } = useCalendarRange(businessId, start, end, staffId, branchId, refreshKey);

  useEffect(() => {
    let active = true;
    getBusinessHours(businessId, branchId)
      .then((h) => active && setHours(h))
      .catch(() => active && setHours([]));
    return () => {
      active = false;
    };
  }, [businessId, branchId]);

  const staffById = useMemo(() => new Map(staff.map((s) => [s.id, s])), [staff]);
  const serviceById = useMemo(() => new Map(services.map((s) => [s.id, s])), [services]);
  const staffColor = useCallback((id: string | null) => (id ? staffById.get(id)?.color ?? null : null), [staffById]);
  const serviceName = useCallback((id: string | null) => (id ? serviceById.get(id)?.name ?? null : null), [serviceById]);
  const durationOf = useCallback(
    (id: string | null) => (id ? serviceById.get(id)?.duration_minutes ?? null : null),
    [serviceById]
  );

  const byDate = useMemo(() => {
    const map = new Map<string, CalendarAppointment[]>();
    for (const a of data) {
      if (prefs.hideCancelled && a.status === "CANCELLED") continue;
      const list = map.get(a.appointment_date);
      if (list) list.push(a);
      else map.set(a.appointment_date, [a]);
    }
    return map;
  }, [data, prefs.hideCancelled]);

  // Izgara: çalışma saatleri, dışında kalan randevular varsa onları da kapsayacak şekilde genişler.
  const [startMin, endMin] = useMemo(() => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const h of hours) {
      if (h.is_closed || !h.open_time || !h.close_time) continue;
      lo = Math.min(lo, timeToMinutes(h.open_time));
      hi = Math.max(hi, timeToMinutes(h.close_time));
    }
    if (!Number.isFinite(lo) || hi <= lo) {
      lo = FALLBACK_START;
      hi = FALLBACK_END;
    }
    if (view !== "MONTH") {
      for (const day of days) {
        for (const a of byDate.get(toISODate(day)) ?? []) {
          const t = toTimed(a, durationOf);
          lo = Math.min(lo, t.start);
          hi = Math.max(hi, t.end);
        }
      }
    }
    return [Math.floor(lo / 60) * 60, Math.min(24 * 60, Math.ceil(hi / 60) * 60)];
  }, [hours, view, days, byDate, durationOf]);

  const openDay = useCallback(
    (iso: string) => {
      onDateChange(iso);
      setView("DAY");
    },
    [onDateChange]
  );

  return (
    <div className="flex flex-col gap-3">
      <CalendarToolbar
        title={rangeTitle(view, days, anchor)}
        view={view}
        loading={loading}
        branches={branches}
        staff={staffInBranch}
        branchId={branchId}
        staffId={staffId}
        hideCancelled={prefs.hideCancelled}
        onPrev={() => onDateChange(toISODate(stepAnchor(view, anchor, -1)))}
        onNext={() => onDateChange(toISODate(stepAnchor(view, anchor, 1)))}
        onToday={() => onDateChange(todayISO())}
        onViewChange={setView}
        onBranchChange={(id) => setPrefs((p) => ({ ...p, branchId: id }))}
        onStaffChange={(id) => setPrefs((p) => ({ ...p, staffId: id }))}
        onHideCancelledChange={(v) => setPrefs((p) => ({ ...p, hideCancelled: v }))}
      />

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>}

      {view === "MONTH" ? (
        <MonthView
          days={days}
          anchor={anchor}
          byDate={byDate}
          staffColor={staffColor}
          serviceName={serviceName}
          narrow={narrow}
          onSelectAppointment={onSelectAppointment}
          onOpenDay={openDay}
        />
      ) : (
        <TimeGridView
          days={days}
          byDate={byDate}
          startMin={startMin}
          endMin={endMin}
          staffColor={staffColor}
          serviceName={serviceName}
          durationOf={durationOf}
          maxColumns={view === "WEEK" && !staffId ? WEEK_MAX_COLUMNS : Infinity}
          onSelectAppointment={onSelectAppointment}
          onSlotClick={onSlotClick}
          onOpenDay={openDay}
        />
      )}
    </div>
  );
}
