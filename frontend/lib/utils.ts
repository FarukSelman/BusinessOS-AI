import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

export function formatDate(dateStr: string | null, includeTime = false) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return includeTime ? d.toLocaleString("tr-TR") : d.toLocaleDateString("tr-TR");
}
