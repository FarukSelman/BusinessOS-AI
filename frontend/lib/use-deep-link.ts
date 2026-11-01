"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

/**
 * Global aramadan gelen bağlantılar (?open=<id>, ?date=...) için: parametreler
 * URL'de göründüğünde handler'ı bir kez çağırır, sonra onları URL'den siler
 * (yenilemede kayıt tekrar açılmasın). Sayfa zaten açıkken gelen yeni bağlantıyı
 * da yakalar, çünkü sayfa yeniden yüklenmez, sadece arama parametreleri değişir.
 *
 * useSearchParams kullandığı için sayfa bir <Suspense> içinde render edilmeli.
 */
export function useDeepLink(keys: readonly string[], handler: (values: Record<string, string>) => void) {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  });

  const signature = keys.map((k) => `${k}=${params.get(k) ?? ""}`).join("&");

  useEffect(() => {
    const values: Record<string, string> = {};
    for (const k of keys) {
      const v = params.get(k);
      if (v) values[k] = v;
    }
    if (Object.keys(values).length === 0) return;
    handlerRef.current(values);
    const next = new URLSearchParams(params.toString());
    for (const k of keys) next.delete(k);
    const qs = next.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
    // signature: yalnızca bu anahtarların değeri değişince
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);
}
