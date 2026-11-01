"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Loader2, Search, X } from "lucide-react";
import { listCustomersPage } from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import type { Customer } from "@/types/customer";

const DEBOUNCE_MS = 250;
const RESULT_LIMIT = 20;

interface Props {
  id?: string;
  /** Seçili müşterinin id'si; boşsa seçim yok. */
  value: string;
  /** value dışarıdan geldiğinde (düzenleme formu) gösterilecek ad. */
  selectedLabel?: string;
  onSelect: (customer: Customer | null) => void;
  placeholder?: string;
  /** Seçim yokken boş bırakılırsa gösterilen ad (ör. "Genel Müşteri"). */
  emptyLabel?: string;
  required?: boolean;
  className?: string;
}

/**
 * Aranabilir müşteri seçimi. Tüm müşterileri yüklemek yerine yazdıkça
 * GET /customers?search= ile en fazla 20 sonuç getirir (Türkçe duyarsız: ad,
 * e-posta, telefon). Klavye: ↑/↓ gez, Enter seç, Esc kapat.
 */
export function CustomerCombobox({
  id,
  value,
  selectedLabel,
  onSelect,
  placeholder = "Ad, telefon veya e-posta ile ara...",
  emptyLabel,
  required,
  className,
}: Props) {
  const businessId = getActiveBusinessId();
  const autoId = useId();
  const inputId = id ?? `${autoId}-input`;
  const listId = `${autoId}-list`;
  const rootRef = useRef<HTMLDivElement>(null);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState<{ id: string; name: string } | null>(null);
  const [results, setResults] = useState<{ key: string; items: Customer[]; total: number } | null>(null);
  const [error, setError] = useState(false);
  const [active, setActive] = useState(0);

  // Seçili müşterinin adı: bu kutuda seçildiyse o, değilse dışarıdan gelen ad.
  const selectedName = !value ? "" : picked?.id === value ? picked.name : (selectedLabel ?? "");
  const key = query.trim();
  const loading = open && results?.key !== key && !error;
  const items = results?.key === key ? results.items : [];

  useEffect(() => {
    if (!open || !businessId) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setError(false);
      listCustomersPage(businessId, { page: 1, size: RESULT_LIMIT, search: key, signal: controller.signal })
        .then((res) => {
          setResults({ key, items: res.items, total: res.total });
          setActive(0);
        })
        .catch(() => {
          if (!controller.signal.aborted) setError(true);
        });
    }, DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [open, key, businessId]);

  // Dışarı tıklayınca kapan.
  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) close();
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  function close() {
    setOpen(false);
    setQuery("");
  }

  function pick(customer: Customer | null) {
    setPicked(customer ? { id: customer.id, name: customer.name } : null);
    onSelect(customer);
    close();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActive((i) => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      if (open && items[active]) {
        e.preventDefault();
        pick(items[active]);
      }
    } else if (e.key === "Escape" && open) {
      e.preventDefault();
      close();
    }
  }

  const more = results?.key === key ? results.total - results.items.length : 0;

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
      <input
        id={inputId}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && items[active] ? `${listId}-${items[active].id}` : undefined}
        autoComplete="off"
        className="flex h-10 w-full rounded-md border border-border bg-surface-elevated pl-9 pr-9 py-2 text-sm text-ink placeholder:text-ink-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        placeholder={value ? selectedName : (emptyLabel ?? placeholder)}
        value={open ? query : selectedName}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        // Form doğrulaması: seçim yoksa boş, seçim varsa ad dolu görünür.
        required={required && !value}
      />
      {value && !open && (
        <button
          type="button"
          aria-label="Müşteri seçimini kaldır"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-ink-muted hover:text-ink"
          onClick={() => pick(null)}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      {open && (
        <div
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 z-50 mt-1 max-h-72 overflow-y-auto rounded-md border border-border bg-surface-elevated shadow-lg"
        >
          {loading ? (
            <p className="flex items-center gap-2 p-3 text-sm text-ink-muted">
              <Loader2 className="h-4 w-4 animate-spin" /> Aranıyor...
            </p>
          ) : error ? (
            <p className="p-3 text-sm text-danger">Müşteriler yüklenemedi.</p>
          ) : items.length === 0 ? (
            <p className="p-3 text-sm text-ink-muted">
              {key ? `"${key}" ile eşleşen müşteri yok.` : "Henüz kayıtlı müşteri yok."}
            </p>
          ) : (
            <>
              {items.map((c, i) => (
                <div
                  key={c.id}
                  id={`${listId}-${c.id}`}
                  role="option"
                  aria-selected={c.id === value}
                  className={cn(
                    "cursor-pointer px-3 py-2 text-sm",
                    i === active ? "bg-accent/10 text-ink" : "text-ink",
                    c.id === value && "font-medium"
                  )}
                  onMouseEnter={() => setActive(i)}
                  // mousedown: input blur'dan önce seç
                  onMouseDown={(e) => {
                    e.preventDefault();
                    pick(c);
                  }}
                >
                  <span className="block truncate">{c.name}</span>
                  {(c.phone || c.email) && (
                    <span className="block truncate text-xs text-ink-muted">{[c.phone, c.email].filter(Boolean).join(" · ")}</span>
                  )}
                </div>
              ))}
              {more > 0 && (
                <p className="border-t border-border px-3 py-2 text-xs text-ink-muted">
                  {more} müşteri daha var, aramayı daraltın.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
