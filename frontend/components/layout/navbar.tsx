"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LogOut, Building2, Bell, CheckCircle2, User, Menu, ArrowLeftRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { 
  logout, 
  getBusiness, 
  listNotifications, 
  getUnreadCount, 
  markNotificationRead, 
  markAllNotificationsRead,
  AppNotification
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { PendingActionsMenu } from "@/components/layout/pending-actions-menu";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { SearchButton } from "@/components/search/search-palette";

export function Navbar({ onMenuClick }: { onMenuClick?: () => void } = {}) {
  const router = useRouter();
  const [businessName, setBusinessName] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    const id = getActiveBusinessId();
    if (!id) return;
    
    getBusiness(id)
      .then((b) => setBusinessName(b.name))
      .catch(() => setBusinessName(null));
      
    // Initial fetch
    fetchNotifications(id);
    
    // Poll every 30 seconds
    const intervalId = setInterval(() => fetchNotifications(id), 30000);
    return () => clearInterval(intervalId);
  }, []);

  async function fetchNotifications(id: string) {
    try {
      const [countRes, notifsRes] = await Promise.all([
        getUnreadCount(id),
        listNotifications(id)
      ]);
      setUnreadCount(countRes.count);
      setNotifications(notifsRes.slice(0, 5)); // show latest 5
    } catch (err) {
      console.error("Bildirimler yüklenemedi", err);
    }
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

  async function handleMarkAsRead(notifId: string) {
    const id = getActiveBusinessId();
    if (!id) return;
    try {
      await markNotificationRead(id, notifId);
      fetchNotifications(id);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleMarkAllRead() {
    const id = getActiveBusinessId();
    if (!id) return;
    try {
      await markAllNotificationsRead(id);
      fetchNotifications(id);
      setShowNotifications(false);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <header className="flex h-16 items-center justify-between gap-2 border-b border-border bg-surface-elevated px-3 sm:px-6">
      <div className="flex min-w-0 items-center gap-2 text-sm text-ink-muted">
        {onMenuClick && (
          <Button variant="ghost" size="icon" className="shrink-0 lg:hidden" onClick={onMenuClick} aria-label="Menüyü aç">
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <Building2 className="hidden h-4 w-4 shrink-0 sm:block" />
        <span className="min-w-[3rem] truncate font-medium text-ink">{businessName ?? "..."}</span>
        {/* Dar ekranda yalnızca ikon: işletme adına yer kalsın */}
        <Link href="/select-business" className="shrink-0 text-ink-muted underline hover:text-ink" aria-label="İşletmeyi değiştir">
          <ArrowLeftRight className="h-4 w-4 sm:hidden" />
          <span className="hidden sm:inline">değiştir</span>
        </Link>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-4">
        <SearchButton />
        <ThemeToggle />
        <PendingActionsMenu />

        <div className="relative">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative"
          >
            <Bell className="h-5 w-5 text-ink-muted hover:text-ink" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[9px] font-bold text-white">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-[min(20rem,calc(100vw-1.5rem))] rounded-lg border border-border bg-surface-elevated/95 backdrop-blur-md shadow-lg z-50 overflow-hidden">
              <div className="flex items-center justify-between border-b border-border p-3">
                <h3 className="font-semibold text-ink">Bildirimler</h3>
                {unreadCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={handleMarkAllRead} className="h-auto p-0 text-xs text-accent-text">
                    Tümünü Okundu İşaretle
                  </Button>
                )}
              </div>
              <div className="max-h-[300px] overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="p-4 text-center text-sm text-ink-muted">Bildirim bulunmuyor.</p>
                ) : (
                  notifications.map((n) => (
                    <div 
                      key={n.id} 
                      className={`flex flex-col gap-1 border-b border-border p-3 last:border-0 hover:bg-surface transition-colors cursor-pointer ${!n.is_read ? 'bg-accent/5' : ''}`}
                      onClick={() => !n.is_read && handleMarkAsRead(n.id)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className={`text-sm font-medium ${!n.is_read ? 'text-ink' : 'text-ink-muted'}`}>
                          {n.title}
                        </span>
                        {!n.is_read && <div className="h-2 w-2 shrink-0 rounded-full bg-accent mt-1.5" />}
                      </div>
                      <p className="text-xs text-ink-muted">{n.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Geniş ekran: profil ve çıkış ayrı; telefonda tek hesap menüsü (işletme adına yer kalsın) */}
        <div className="hidden items-center gap-4 sm:flex">
          <Link href="/profile">
            <Button variant="ghost" size="icon" aria-label="Profil">
              <User className="h-5 w-5 text-ink-muted hover:text-ink" />
            </Button>
          </Link>

          <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2" aria-label="Çıkış yap">
            <LogOut className="h-4 w-4" />
            <span>Çıkış yap</span>
          </Button>
        </div>
        <AccountMenu className="sm:hidden" onLogout={handleLogout} />
      </div>
    </header>
  );
}

function AccountMenu({ onLogout, className }: { onLogout: () => void; className?: string }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className={`relative ${className ?? ""}`}>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Hesap menüsü"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <User className="h-5 w-5 text-ink-muted hover:text-ink" />
      </Button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-44 overflow-hidden rounded-lg border border-border bg-surface-elevated shadow-lg"
        >
          <Link
            href="/profile"
            role="menuitem"
            className="flex items-center gap-2 px-3 py-2.5 text-sm text-ink hover:bg-surface"
            onClick={() => setOpen(false)}
          >
            <User className="h-4 w-4 text-ink-muted" /> Profil
          </Link>
          <button
            type="button"
            role="menuitem"
            className="flex w-full items-center gap-2 border-t border-border px-3 py-2.5 text-left text-sm text-danger hover:bg-surface"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
          >
            <LogOut className="h-4 w-4" /> Çıkış yap
          </button>
        </div>
      )}
    </div>
  );
}
