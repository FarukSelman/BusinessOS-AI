"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { PendingActionCard } from "@/components/chat/pending-action-card";
import {
  AGENT_ACTIONS_CHANGED,
  AgentActionRecord,
  ApiError,
  approveAgentAction,
  listPendingAgentActions,
  notifyAgentActionsChanged,
  rejectAgentAction,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";

function timeAgo(iso: string): string {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return "az önce";
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} saat önce`;
  return `${Math.round(hours / 24)} gün önce`;
}

/**
 * Navbar button + panel listing every agent draft that waits for approval,
 * so drafts are not lost when the user leaves the chat where they were made.
 */
export function PendingActionsMenu() {
  const [actions, setActions] = useState<AgentActionRecord[]>([]);
  const [open, setOpen] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [available, setAvailable] = useState(true);
  const panelRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    const businessId = getActiveBusinessId();
    if (!businessId) return;
    try {
      setActions(await listPendingAgentActions(businessId));
      setAvailable(true);
    } catch (err) {
      // Roles without access (403) simply do not get the button.
      if (err instanceof ApiError && err.status === 403) setAvailable(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial load from the API
    refresh();
    const interval = setInterval(refresh, 30000);
    window.addEventListener(AGENT_ACTIONS_CHANGED, refresh);
    window.addEventListener("focus", refresh);
    return () => {
      clearInterval(interval);
      window.removeEventListener(AGENT_ACTIONS_CHANGED, refresh);
      window.removeEventListener("focus", refresh);
    };
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function resolve(actionId: string, run: (businessId: string) => Promise<unknown>, success: string) {
    const businessId = getActiveBusinessId();
    if (!businessId) return;
    setBusyId(actionId);
    try {
      await run(businessId);
      toast.success(success);
      setActions((prev) => prev.filter((a) => a.id !== actionId));
      notifyAgentActionsChanged();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem tamamlanamadı.");
      refresh();
    } finally {
      setBusyId(null);
    }
  }

  if (!available) return null;
  const count = actions.length;

  return (
    <div className="relative" ref={panelRef}>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        className="relative"
        title="Onay bekleyen işlemler"
        aria-label={`Onay bekleyen işlemler (${count})`}
        aria-expanded={open}
      >
        <ClipboardCheck className="h-5 w-5 text-ink-muted hover:text-ink" />
        {count > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500 px-1 text-[9px] font-bold text-white">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-[min(26rem,calc(100vw-2rem))] overflow-hidden rounded-lg border border-border bg-surface-elevated/95 shadow-lg backdrop-blur-md">
          <div className="border-b border-border p-3">
            <h3 className="font-semibold text-ink">Onay bekleyen işlemler</h3>
            <p className="text-xs text-ink-muted">Ajanların hazırladığı taslaklar onaylanınca uygulanır.</p>
          </div>
          <div className="max-h-[70vh] overflow-y-auto p-3">
            {count === 0 ? (
              <p className="p-4 text-center text-sm text-ink-muted">Onay bekleyen işlem yok.</p>
            ) : (
              actions.map((action) => (
                <div key={action.id} className="mb-3 last:mb-0">
                  <p className="text-[11px] text-ink-muted">
                    {action.requested_by_name ?? "Bir ekip üyesi"} · {timeAgo(action.created_at)}
                  </p>
                  <PendingActionCard
                    action={{ action_id: action.id, action_type: action.action_type, payload: action.payload }}
                    disabled={busyId === action.id}
                    onApprove={(id) =>
                      resolve(id, (b) => approveAgentAction(b, id), "Onaylandı ve uygulandı.")
                    }
                    onReject={(id, reason) =>
                      resolve(id, (b) => rejectAgentAction(b, id, reason), "Reddedildi.")
                    }
                  />
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
