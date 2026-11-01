"use client";

import { Lock } from "lucide-react";
import { useMyAccess } from "@/lib/use-my-access";

/**
 * Yalnızca finans rollerine (sahip, yönetici) açık sayfalar. Rol yüklenene kadar
 * içerik oluşturulmaz; böylece yetkisiz kullanıcı için arka planda 403 alacak
 * istekler de gitmez. Backend aynı kuralı require_finance ile ayrıca uygular.
 */
export function FinanceOnly({ children }: { children: React.ReactNode }) {
  const access = useMyAccess();

  if (access === null) {
    return <p className="text-sm text-ink-muted">Yükleniyor...</p>;
  }
  if (!access.can_view_finance) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-lg border border-border bg-surface-elevated px-6 py-12 text-center">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface text-ink-muted">
          <Lock className="h-5 w-5" />
        </span>
        <h1 className="font-display text-lg font-semibold text-ink">Bu sayfaya erişiminiz yok</h1>
        <p className="text-sm text-ink-muted">Bu sayfa yalnızca işletme sahibi ve yöneticilere açıktır.</p>
      </div>
    );
  }
  return <>{children}</>;
}
