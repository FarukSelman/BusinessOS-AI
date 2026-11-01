import { todayISO } from "./date";

/** Dışa aktarımda bir istekte çekilen kayıt sayısı. */
export const EXPORT_PAGE_SIZE = 500;
/** Tarayıcıyı kilitlememek için tek dışa aktarımda en fazla bu kadar kayıt. */
export const EXPORT_MAX_ROWS = 20_000;

/**
 * Sayfalı bir listeyi baştan sona çeker: boyutu pageSize'dan küçük bir sayfa
 * gelene kadar devam eder. Liste uç noktalarının sıralaması id ile kararlı
 * olmalı, yoksa sayfalar arasında kayıt tekrarlanır ya da kaybolur.
 */
export async function fetchAllPages<T>(
  fetchPage: (page: number, size: number) => Promise<T[]>,
  pageSize = EXPORT_PAGE_SIZE,
  maxRows = EXPORT_MAX_ROWS
): Promise<{ rows: T[]; truncated: boolean }> {
  const rows: T[] = [];
  for (let page = 1; ; page++) {
    const batch = await fetchPage(page, pageSize);
    rows.push(...batch);
    if (batch.length < pageSize) return { rows, truncated: false };
    if (rows.length >= maxRows) return { rows: rows.slice(0, maxRows), truncated: true };
  }
}

/**
 * Excel/Sheets "=", "+", "-", "@" (ve sekme/CR) ile başlayan hücreyi formül
 * sayar; online randevudan gelen bir müşteri adı böylece komut çalıştırabilir.
 * Başına ' koyarak metin olarak kalmasını sağlıyoruz.
 */
function csvCell(value: unknown): string {
  let text = (value ?? "").toString();
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return `"${text.replace(/"/g, '""')}"`;
}

export function exportToCSV(filename: string, headers: string[], rows: string[][]) {
  // Add BOM for Turkish characters in Excel
  const BOM = '﻿';
  const csv = BOM + [
    headers.map(csvCell).join(';'),
    ...rows.map(row => row.map(csvCell).join(';'))
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}_${todayISO()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
