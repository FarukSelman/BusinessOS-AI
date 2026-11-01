"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  page: number;
  pageCount: number;
  total: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
}

/** "Önceki · Sayfa 3 / 12 · 234 kayıt · Sonraki" */
export function Pagination({ page, pageCount, total, loading, onPageChange }: Props) {
  return (
    <nav className="flex flex-wrap items-center justify-between gap-2" aria-label="Sayfalama">
      <span className="text-sm text-ink-muted tabular-nums">{total.toLocaleString("tr-TR")} kayıt</span>
      {pageCount > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1 || loading}
            onClick={() => onPageChange(page - 1)}
            aria-label="Önceki sayfa"
          >
            <ChevronLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Önceki</span>
          </Button>
          <span className="text-sm text-ink-muted tabular-nums">
            Sayfa {page} / {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount || loading}
            onClick={() => onPageChange(page + 1)}
            aria-label="Sonraki sayfa"
          >
            <span className="hidden sm:inline">Sonraki</span>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </nav>
  );
}
