import type { AppointmentStatus } from "@/lib/api";

// Anlamsal tema renkleri: iki temada da metin olarak okunur (WCAG AA).
// soft: rozet zemini (üstünde color ile yazı 4.5:1 geçer).
export const statusStyles: Record<AppointmentStatus, { label: string; color: string; soft: string }> = {
  PENDING: { label: "Beklemede", color: "var(--warning)", soft: "var(--warning-soft)" },
  CONFIRMED: { label: "Onaylandı", color: "var(--success)", soft: "var(--success-soft)" },
  CANCELLED: { label: "İptal edildi", color: "var(--danger)", soft: "var(--danger-soft)" },
  COMPLETED: { label: "Tamamlandı", color: "var(--neutral)", soft: "var(--neutral-soft)" },
  NO_SHOW: { label: "Gelmedi", color: "var(--violet)", soft: "var(--violet-soft)" },
};

/** Durum renginin hafif zemin tonu. */
export function statusTint(color: string, percent = 15): string {
  return `color-mix(in srgb, ${color} ${percent}%, transparent)`;
}
