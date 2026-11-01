"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { ApiError } from "./api";
import { EXPORT_MAX_ROWS, exportToCSV, fetchAllPages } from "./export";

/** Sayfalı bir listenin tamamını çekip CSV indirir; çalışırken exporting=true olur. */
export function useCsvExport() {
  const [exporting, setExporting] = useState(false);

  const run = useCallback(
    async <T,>(
      filename: string,
      headers: string[],
      fetchPage: (page: number, size: number) => Promise<T[]>,
      toRow: (item: T) => string[]
    ) => {
      setExporting(true);
      try {
        const { rows, truncated } = await fetchAllPages(fetchPage);
        exportToCSV(filename, headers, rows.map(toRow));
        if (truncated) {
          toast.warning(`İlk ${EXPORT_MAX_ROWS.toLocaleString("tr-TR")} kayıt dışa aktarıldı.`);
        }
      } catch (err) {
        toast.error(err instanceof ApiError ? err.message : "Dışa aktarılamadı.");
      } finally {
        setExporting(false);
      }
    },
    []
  );

  return { exporting, run };
}
