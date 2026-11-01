import type { AppointmentStatus } from "@/lib/api";

export const statusStyles: Record<AppointmentStatus, { label: string; color: string }> = {
  PENDING: { label: "Beklemede", color: "var(--agent-appointments)" },
  CONFIRMED: { label: "Onaylandı", color: "var(--agent-sales)" },
  CANCELLED: { label: "İptal edildi", color: "var(--danger)" },
  COMPLETED: { label: "Tamamlandı", color: "var(--ink-muted)" },
  NO_SHOW: { label: "Gelmedi", color: "var(--agent-marketing)" },
};

/** Durum renginin hafif zemin tonu. */
export function statusTint(color: string, percent = 15): string {
  return `color-mix(in srgb, ${color} ${percent}%, transparent)`;
}
