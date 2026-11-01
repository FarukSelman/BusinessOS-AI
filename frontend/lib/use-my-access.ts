"use client";

import { useEffect, useState } from "react";
import { getMyAccess, type MyBusinessAccess } from "./api";
import { getActiveBusinessId } from "./business";

// İşletme başına bir kez çekilir; aynı oturumda sayfalar arası paylaşılır.
const cache = new Map<string, Promise<MyBusinessAccess>>();

/**
 * Aktif işletmedeki rolüm. Yüklenene kadar null: tutarları ve fatura işlemlerini
 * gösterip gizlerken null'ı "yetki yok" saymak, bir an yanlış bilgi göstermekten iyidir.
 */
export function useMyAccess(): MyBusinessAccess | null {
  const businessId = getActiveBusinessId();
  const [access, setAccess] = useState<{ businessId: string; value: MyBusinessAccess } | null>(null);

  useEffect(() => {
    if (!businessId) return;
    let request = cache.get(businessId);
    if (!request) {
      request = getMyAccess(businessId);
      cache.set(businessId, request);
      request.catch(() => cache.delete(businessId));
    }
    let active = true;
    request.then((value) => active && setAccess({ businessId, value })).catch(() => {});
    return () => {
      active = false;
    };
  }, [businessId]);

  return access && access.businessId === businessId ? access.value : null;
}
