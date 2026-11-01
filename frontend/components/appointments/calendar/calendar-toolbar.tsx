"use client";

import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import type { Branch, StaffProfile } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CalendarView } from "./layout";

const VIEWS: { value: CalendarView; label: string }[] = [
  { value: "DAY", label: "Gün" },
  { value: "WEEK", label: "Hafta" },
  { value: "MONTH", label: "Ay" },
];

interface Props {
  title: string;
  view: CalendarView;
  loading: boolean;
  branches: Branch[];
  staff: StaffProfile[];
  branchId: string | null;
  staffId: string | null;
  hideCancelled: boolean;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
  onViewChange: (view: CalendarView) => void;
  onBranchChange: (id: string | null) => void;
  onStaffChange: (id: string | null) => void;
  onHideCancelledChange: (value: boolean) => void;
}

export function CalendarToolbar(props: Props) {
  const { title, view, loading, branches, staff, branchId, staffId, hideCancelled } = props;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <Button variant="outline" size="icon" onClick={props.onPrev} aria-label="Önceki">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={props.onNext} aria-label="Sonraki">
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button variant="outline" onClick={props.onToday}>
            Bugün
          </Button>
          <h2 className="ml-1 min-w-0 text-base font-semibold text-ink sm:text-lg">{title}</h2>
          {loading && <Loader2 className="h-4 w-4 animate-spin text-ink-muted" aria-label="Yükleniyor" />}
        </div>

        <div className="flex rounded-md border border-border bg-surface-elevated p-1" role="tablist">
          {VIEWS.map((v) => (
            <button
              key={v.value}
              type="button"
              role="tab"
              aria-selected={view === v.value}
              onClick={() => props.onViewChange(v.value)}
              className={cn(
                "rounded px-3 py-1.5 text-xs font-medium transition-colors",
                view === v.value ? "bg-accent text-white" : "text-ink-muted hover:text-ink"
              )}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {branches.length > 1 && (
          <Select
            aria-label="Şube"
            value={branchId ?? ""}
            onChange={(e) => props.onBranchChange(e.target.value || null)}
            className="h-9 w-auto min-w-[9rem]"
          >
            <option value="">Tüm şubeler</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
        )}
        {staff.length > 0 && (
          <Select
            aria-label="Personel"
            value={staffId ?? ""}
            onChange={(e) => props.onStaffChange(e.target.value || null)}
            className="h-9 w-auto min-w-[9rem]"
          >
            <option value="">Tüm personel</option>
            {staff.map((s) => (
              <option key={s.id} value={s.id}>
                {s.full_name}
              </option>
            ))}
          </Select>
        )}
        <label className="flex cursor-pointer select-none items-center gap-2 text-sm text-ink-muted">
          <input
            type="checkbox"
            checked={hideCancelled}
            onChange={(e) => props.onHideCancelledChange(e.target.checked)}
            className="h-4 w-4 accent-[var(--accent)]"
          />
          İptalleri gizle
        </label>
      </div>
    </div>
  );
}
