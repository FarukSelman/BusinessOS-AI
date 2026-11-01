"use client";

import { memo } from "react";
import type { CalendarAppointment } from "@/lib/api";
import { toHm } from "@/lib/date";
import { cn } from "@/lib/utils";
import { statusStyles, statusTint } from "../constants";

interface Props {
  appt: CalendarAppointment;
  staffColor: string | null;
  serviceName: string | null;
  /** Saat ızgarasında konumlandırma; ay görünümünde verilmez. */
  style?: React.CSSProperties;
  /** Blok iki satır sığacak kadar yüksek mi. */
  roomy?: boolean;
  compact?: boolean;
  onSelect: (id: string) => void;
}

/**
 * Zemin rengi durumdan, sol kenar rengi personelden gelir.
 * İptal: soluk + üstü çizili. Gelmedi: kesikli çerçeve.
 */
function AppointmentBlockImpl({ appt, staffColor, serviceName, style, roomy, compact, onSelect }: Props) {
  const status = statusStyles[appt.status];
  const cancelled = appt.status === "CANCELLED";
  const noShow = appt.status === "NO_SHOW";
  const title = `${toHm(appt.start_time)}${appt.end_time ? `–${toHm(appt.end_time)}` : ""} · ${appt.customer_name}${
    serviceName ? ` · ${serviceName}` : ""
  } · ${status.label}`;

  return (
    <button
      type="button"
      title={title}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(appt.id);
      }}
      className={cn(
        "overflow-hidden rounded-[4px] border-l-[3px] text-left text-ink transition-[filter] hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        style ? "absolute px-1.5 py-0.5" : "flex w-full items-center gap-1 px-1 py-0.5",
        compact ? "text-[10px]" : "text-[11px]",
        cancelled && "opacity-55 line-through"
      )}
      style={{
        ...style,
        backgroundColor: statusTint(status.color, cancelled ? 10 : 18),
        borderLeftColor: staffColor ?? status.color,
        outline: noShow ? `1px dashed ${status.color}` : undefined,
        outlineOffset: noShow ? -1 : undefined,
      }}
    >
      <span className="block truncate leading-tight">
        <span className="font-semibold tabular-nums">{toHm(appt.start_time)}</span> {appt.customer_name}
      </span>
      {roomy && serviceName && <span className="block truncate leading-tight text-ink-muted">{serviceName}</span>}
    </button>
  );
}

export const AppointmentBlock = memo(AppointmentBlockImpl);
