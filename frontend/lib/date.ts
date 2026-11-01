import { format, parseISO } from "date-fns";

// Tarihler hep yerel saatle: toISOString() UTC'ye çevirir ve Türkiye'de
// 00:00–03:00 arası "bugün"ü bir önceki güne kaydırır.

export function toISODate(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

export function todayISO(): string {
  return toISODate(new Date());
}

/** "YYYY-MM-DD" → yerel gece yarısı (new Date("YYYY-MM-DD") UTC sayılır). */
export function fromISODate(s: string): Date {
  return parseISO(s);
}

/** "HH:MM:SS" → "HH:MM" */
export function toHm(t: string): string {
  return t.slice(0, 5);
}

/** <input type="time"> "HH:MM" döndürür, backend "HH:MM:SS" bekliyor. */
export function toHms(t: string): string {
  return t.length === 5 ? `${t}:00` : t;
}

export function timeToMinutes(t: string): number {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + (m || 0);
}

export function minutesToHm(total: number): string {
  const clamped = Math.max(0, Math.min(total, 24 * 60 - 1));
  return `${String(Math.floor(clamped / 60)).padStart(2, "0")}:${String(clamped % 60).padStart(2, "0")}`;
}

export function addMinutes(hm: string, minutes: number): string {
  return minutesToHm(timeToMinutes(hm) + minutes);
}
