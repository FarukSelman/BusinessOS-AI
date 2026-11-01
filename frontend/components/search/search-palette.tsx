"use client";

import { createContext, useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { CalendarClock, FileText, Loader2, Package, Search, User as UserIcon, CornerDownLeft } from "lucide-react";
import { ApiError, globalSearch, type SearchResponse } from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { fromISODate, toHm } from "@/lib/date";
import { formatCurrency, cn } from "@/lib/utils";
import { navGroups } from "@/components/layout/sidebar";
import { statusStyles } from "@/components/appointments/constants";

const MIN_QUERY = 2;
const DEBOUNCE_MS = 250;
const MAX_PAGES = 5;

const INVOICE_STATUS: Record<string, string> = {
  DRAFT: "Taslak",
  SENT: "Gönderildi",
  PAID: "Ödendi",
  OVERDUE: "Gecikmiş",
  CANCELLED: "İptal",
};

/** Backend aramasıyla aynı katlama: "ayse" ↔ "Ayşe", "isik" ↔ "IŞIK". */
function fold(value: string) {
  return value
    .replace(/[Iİı]/g, "i")
    .replace(/[Şş]/g, "s")
    .replace(/[Ğğ]/g, "g")
    .replace(/[Çç]/g, "c")
    .replace(/[Öö]/g, "o")
    .replace(/[Üü]/g, "u")
    .toLowerCase();
}

const PAGES = navGroups.flatMap((g) => g.items.map((i) => ({ ...i, group: g.label })));

// ---------------------------------------------------------------- context

interface SearchPaletteContext {
  open: () => void;
}

const Ctx = createContext<SearchPaletteContext | null>(null);

export function useSearchPalette() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSearchPalette, SearchPaletteProvider içinde kullanılmalı");
  return ctx;
}

/**
 * Ctrl+K / Cmd+K ile her yerden (bir input'a yazarken de) açılır. Tarayıcının
 * adres çubuğu kısayolunu panelde bilerek ezer.
 */
export function SearchPaletteProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isK = e.code === "KeyK" || e.key.toLowerCase() === "k";
      if (isK && (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey) {
        e.preventDefault();
        setIsOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const open = useCallback(() => setIsOpen(true), []);

  return (
    <Ctx.Provider value={{ open }}>
      {children}
      <DialogPrimitive.Root open={isOpen} onOpenChange={setIsOpen}>
        {isOpen && <SearchPalette onClose={() => setIsOpen(false)} />}
      </DialogPrimitive.Root>
    </Ctx.Provider>
  );
}

// ---------------------------------------------------------------- palette

interface ResultItem {
  key: string;
  href: string;
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  meta?: React.ReactNode;
}

interface ResultGroup {
  key: string;
  label: string;
  items: ResultItem[];
  /** Gösterilenden fazlası varsa listedeki tam sonuç bağlantısı. */
  more?: { count: number; href?: string };
}

function buildGroups(query: string, data: SearchResponse | null): ResultGroup[] {
  const groups: ResultGroup[] = [];
  const q = fold(query.trim());
  const pages = (q ? PAGES.filter((p) => fold(p.label).includes(q) || fold(p.group).includes(q)) : PAGES).slice(
    0,
    q ? MAX_PAGES : 8
  );
  const enc = encodeURIComponent;

  if (data) {
    const { customers, appointments, invoices, products } = data;
    if (customers.items.length) {
      groups.push({
        key: "customers",
        label: "Müşteriler",
        items: customers.items.map((c) => ({
          key: `c-${c.id}`,
          href: `/customers?open=${c.id}`,
          icon: <UserIcon className="h-4 w-4" />,
          title: c.name,
          subtitle: [c.phone, c.email].filter(Boolean).join(" · ") || undefined,
        })),
        more: { count: customers.total - customers.items.length, href: `/customers?q=${enc(query.trim())}` },
      });
    }
    if (appointments.items.length) {
      groups.push({
        key: "appointments",
        label: "Randevular",
        items: appointments.items.map((a) => ({
          key: `a-${a.id}`,
          href: `/appointments?date=${a.appointment_date}&open=${a.id}`,
          icon: <CalendarClock className="h-4 w-4" />,
          title: a.customer_name,
          subtitle: `${format(fromISODate(a.appointment_date), "d MMM yyyy, EEE", { locale: tr })} · ${toHm(a.start_time)}`,
          meta: (
            <span
              className="rounded-full px-2 py-0.5 text-[11px] font-medium"
              style={{ backgroundColor: statusStyles[a.status].soft, color: statusStyles[a.status].color }}
            >
              {statusStyles[a.status].label}
            </span>
          ),
        })),
        more: { count: appointments.total - appointments.items.length },
      });
    }
    if (invoices.items.length) {
      groups.push({
        key: "invoices",
        label: "Faturalar",
        items: invoices.items.map((i) => ({
          key: `i-${i.id}`,
          href: `/invoices?q=${enc(i.invoice_number)}&open=${i.id}`,
          icon: <FileText className="h-4 w-4" />,
          title: i.invoice_number,
          subtitle: `${i.customer_name} · ${INVOICE_STATUS[i.status] ?? i.status}`,
          // Çalışan/izleyici rolünde tutar gelmez (backend null döner).
          meta: i.total_amount !== null ? <span className="tabular-nums text-ink">{formatCurrency(i.total_amount)}</span> : undefined,
        })),
        more: { count: invoices.total - invoices.items.length, href: `/invoices?q=${enc(query.trim())}` },
      });
    }
    if (products.items.length) {
      groups.push({
        key: "products",
        label: "Ürünler",
        items: products.items.map((p) => ({
          key: `p-${p.id}`,
          href: `/products?q=${enc(p.sku || p.name)}`,
          icon: <Package className="h-4 w-4" />,
          title: p.name,
          subtitle: [p.sku, `Stok: ${p.current_stock}`].filter(Boolean).join(" · "),
        })),
        more: { count: products.total - products.items.length, href: `/products?q=${enc(query.trim())}` },
      });
    }
  }

  if (pages.length) {
    groups.push({
      key: "pages",
      label: "Sayfalar",
      items: pages.map((p) => {
        const Icon = p.icon;
        return {
          key: `page-${p.href}`,
          href: p.href,
          icon: <Icon className="h-4 w-4" style={{ color: p.color }} />,
          title: p.label,
          subtitle: p.group,
        };
      }),
    });
  }
  return groups;
}

function SearchPalette({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const businessId = getActiveBusinessId();
  const listId = useId();
  const listRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<{ query: string; data: SearchResponse | null; error: string | null } | null>(
    null
  );
  const [active, setActive] = useState(0);

  const trimmed = query.trim();
  const searchable = trimmed.length >= MIN_QUERY && !!businessId;

  // Yazmayı bitirince tek istek; yeni harf gelince eskisi iptal edilir.
  useEffect(() => {
    if (!searchable) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      globalSearch(businessId!, trimmed, controller.signal)
        .then((data) => setResult({ query: trimmed, data, error: null }))
        .catch((err) => {
          if (controller.signal.aborted) return;
          setResult({ query: trimmed, data: null, error: err instanceof ApiError ? err.message : "Arama yapılamadı." });
        });
    }, DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [businessId, trimmed, searchable]);

  const current = searchable && result?.query === trimmed ? result : null;
  const loading = searchable && !current;
  const groups = useMemo(() => buildGroups(query, current?.data ?? null), [query, current]);
  const flat = useMemo(() => groups.flatMap((g) => g.items), [groups]);
  const activeIndex = flat.length ? Math.min(active, flat.length - 1) : -1;
  const activeItem = activeIndex >= 0 ? flat[activeIndex] : null;
  const optionId = (key: string) => `${listId}-${key}`;

  useEffect(() => {
    if (!activeItem) return;
    document.getElementById(optionId(activeItem.key))?.scrollIntoView({ block: "nearest" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeItem?.key]);

  function go(href: string) {
    onClose();
    router.push(href);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!flat.length) return;
      const step = e.key === "ArrowDown" ? 1 : -1;
      setActive((activeIndex + step + flat.length) % flat.length);
    } else if (e.key === "Enter" && activeItem) {
      e.preventDefault();
      go(activeItem.href);
    }
  }

  const resultCount = current?.data
    ? current.data.customers.total + current.data.appointments.total + current.data.invoices.total + current.data.products.total
    : 0;

  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/40" />
      <DialogPrimitive.Content
        className="fixed left-1/2 top-[10vh] z-50 flex max-h-[75vh] w-[calc(100%-2rem)] max-w-xl -translate-x-1/2 flex-col overflow-hidden rounded-xl border border-border bg-surface-elevated shadow-2xl outline-none"
        aria-describedby={undefined}
        onOpenAutoFocus={(e) => {
          e.preventDefault();
          (e.currentTarget as HTMLElement).querySelector("input")?.focus();
        }}
      >
        <DialogPrimitive.Title className="sr-only">Ara</DialogPrimitive.Title>
        <div className="flex items-center gap-2 border-b border-border px-4">
          <Search className="h-4 w-4 shrink-0 text-ink-muted" />
          <input
            role="combobox"
            aria-expanded={flat.length > 0}
            aria-controls={listId}
            aria-activedescendant={activeItem ? optionId(activeItem.key) : undefined}
            aria-autocomplete="list"
            aria-label="Müşteri, randevu, fatura, ürün veya sayfa ara"
            placeholder="Müşteri, randevu, fatura, ürün veya sayfa ara…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            onKeyDown={onKeyDown}
            className="h-12 min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
          />
          {loading && <Loader2 className="h-4 w-4 shrink-0 animate-spin text-ink-muted" aria-label="Aranıyor" />}
        </div>

        <div ref={listRef} id={listId} role="listbox" aria-label="Arama sonuçları" className="overflow-y-auto p-2">
          {current?.error && <p className="px-3 py-6 text-center text-sm text-danger">{current.error}</p>}
          {trimmed.length > 0 && trimmed.length < MIN_QUERY && (
            <p className="px-3 pb-1 pt-2 text-xs text-ink-muted">Kayıtları aramak için en az {MIN_QUERY} harf yazın.</p>
          )}
          {searchable && current?.data && resultCount === 0 && (
            <p className="px-3 pb-1 pt-2 text-sm text-ink-muted">
              &quot;{trimmed}&quot; için kayıt bulunamadı.
            </p>
          )}

          {groups.map((g) => (
            <div key={g.key} role="group" aria-labelledby={`${listId}-g-${g.key}`} className="py-1">
              <div id={`${listId}-g-${g.key}`} className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
                {g.label}
              </div>
              {g.items.map((item) => {
                const selected = item.key === activeItem?.key;
                return (
                  <div
                    key={item.key}
                    id={optionId(item.key)}
                    role="option"
                    aria-selected={selected}
                    onMouseMove={() => setActive(flat.indexOf(item))}
                    onClick={() => go(item.href)}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm",
                      selected ? "bg-surface text-ink" : "text-ink"
                    )}
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-surface text-ink-muted">
                      {item.icon}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{item.title}</span>
                      {item.subtitle && <span className="block truncate text-xs text-ink-muted">{item.subtitle}</span>}
                    </span>
                    {item.meta}
                    {selected && <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-ink-muted" aria-hidden />}
                  </div>
                );
              })}
              {g.more && g.more.count > 0 && (
                g.more.href ? (
                  <button
                    type="button"
                    onClick={() => go(g.more!.href!)}
                    className="ml-3 mt-1 text-xs font-medium text-accent-text hover:underline"
                  >
                    {g.more.count} sonuç daha → listede gör
                  </button>
                ) : (
                  <p className="ml-3 mt-1 text-xs text-ink-muted">+{g.more.count} kayıt daha</p>
                )
              )}
            </div>
          ))}
        </div>

        <div className="hidden items-center gap-4 border-t border-border px-4 py-2 text-[11px] text-ink-muted sm:flex">
          <span><Kbd>↑</Kbd> <Kbd>↓</Kbd> gezin</span>
          <span><Kbd>Enter</Kbd> aç</span>
          <span><Kbd>Esc</Kbd> kapat</span>
        </div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 font-sans text-[10px] font-medium text-ink-muted">
      {children}
    </kbd>
  );
}

/** Navbar düğmesi: 768px ve üstünde "Ara… Ctrl K", daha dar ekranda sadece ikon. */
export function SearchButton() {
  const { open } = useSearchPalette();
  const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);
  return (
    <button
      type="button"
      onClick={open}
      aria-label="Ara (Ctrl+K)"
      className="flex h-10 items-center gap-2 rounded-md text-sm text-ink-muted hover:text-ink md:h-9 md:w-48 md:border md:border-border md:bg-surface md:px-3 lg:w-56"
    >
      <Search className="h-5 w-5 md:h-4 md:w-4" />
      <span className="hidden flex-1 text-left md:inline">Ara…</span>
      <span className="hidden md:inline">
        <Kbd>{isMac ? "⌘K" : "Ctrl K"}</Kbd>
      </span>
    </button>
  );
}
