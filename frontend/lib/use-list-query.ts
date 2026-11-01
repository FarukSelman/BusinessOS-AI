"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ApiError, LIST_PAGE_SIZE, type Page } from "./api";

const SEARCH_DEBOUNCE_MS = 300;

export interface ListQuery {
  page: number;
  search: string;
  /** Sayfanın kendi filtreleri (URL'de aynı adla tutulur). */
  filters: Record<string, string>;
  signal: AbortSignal;
}

interface Loaded<T> {
  key: string;
  items: T[];
  total: number;
  error: string | null;
}

/**
 * Sayfalı + aramalı liste. Sayfa, arama (?q=) ve filtreler URL'de durur; yenileme
 * ve geri tuşunda kaybolmaz. Değişiklikler router.replace ile yazılır (her tuş
 * geçmişe eklenmez). Arama 300 ms bekler; arama/filtre değişince sayfa 1'e döner;
 * eski istek iptal edilir. Yeni sayfa gelene kadar önceki kayıtlar gösterilir.
 *
 * useSearchParams kullandığı için sayfa bir <Suspense> içinde render edilmeli.
 */
export function useListQuery<T>(
  filterKeys: readonly string[],
  fetchPage: (query: ListQuery) => Promise<Page<T>>,
  enabled = true
) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const page = Math.max(1, Number(params.get("page")) || 1);
  const search = params.get("q") ?? "";
  const filters: Record<string, string> = {};
  for (const k of filterKeys) filters[k] = params.get(k) ?? "";

  const [searchInput, setSearchInput] = useState(search);
  const [reloadKey, setReloadKey] = useState(0);
  const [loaded, setLoaded] = useState<Loaded<T> | null>(null);

  const replaceParams = useCallback(
    (changes: Record<string, string | null>) => {
      const next = new URLSearchParams(params.toString());
      for (const [k, v] of Object.entries(changes)) {
        if (v) next.set(k, v);
        else next.delete(k);
      }
      const qs = next.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    },
    [params, pathname, router]
  );

  // Yazılan aramayı bekletip URL'ye yaz (sayfa 1'e dön).
  useEffect(() => {
    if (searchInput.trim() === search) return;
    const id = window.setTimeout(() => replaceParams({ q: searchInput.trim() || null, page: null }), SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(id);
  }, [searchInput, search, replaceParams]);

  const filtersKey = filterKeys.map((k) => `${k}=${filters[k]}`).join("&");
  const key = `${page}|${search}|${filtersKey}|${reloadKey}`;

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    fetchPage({ page, search, filters: Object.fromEntries(new URLSearchParams(filtersKey)), signal: controller.signal })
      .then((res) => setLoaded({ key, items: res.items, total: res.total, error: null }))
      .catch((err) => {
        if (controller.signal.aborted) return;
        setLoaded((prev) => ({
          key,
          items: prev?.items ?? [],
          total: prev?.total ?? 0,
          error:
            err instanceof ApiError && err.status === 422
              ? "Bağlantıdaki arama/filtre geçersiz. Filtreleri temizleyip tekrar deneyin."
              : err instanceof ApiError
                ? err.message
                : "Liste yüklenemedi.",
        }));
      });
    return () => controller.abort();
    // fetchPage her render'da yeni olabilir; isteği yalnızca sorgu değişince at.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, enabled]);

  const total = loaded?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / LIST_PAGE_SIZE));

  // Son sayfadaki kayıtlar silinince boş bir sayfada kalma.
  useEffect(() => {
    if (loaded?.key === key && !loaded.error && loaded.items.length === 0 && page > pageCount) {
      replaceParams({ page: pageCount > 1 ? String(pageCount) : null });
    }
  }, [loaded, key, page, pageCount, replaceParams]);

  return {
    items: loaded?.items ?? [],
    total,
    page,
    pageCount,
    /** İlk yükleme mi (gösterilecek veri yok). */
    initialLoading: loaded === null,
    /** Yeni sorgunun sonucu henüz gelmedi (önceki veri ekranda). */
    loading: loaded?.key !== key,
    error: loaded?.key === key ? loaded.error : null,
    search,
    searchInput,
    setSearchInput,
    filters,
    setFilter: (name: string, value: string) => replaceParams({ [name]: value || null, page: null }),
    setPage: (p: number) => replaceParams({ page: p > 1 ? String(p) : null }),
    /** Kayıt ekleme/silme sonrası aynı sayfayı yeniden çek. */
    reload: () => setReloadKey((k) => k + 1),
  };
}
