"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { PendingAgentAction } from "@/lib/api";

const ACTION_TITLES: Record<string, string> = {
  CREATE_APPOINTMENT: "Randevu oluşturma",
  CANCEL_APPOINTMENT: "Randevu iptali",
  CREATE_INVOICE: "Fatura taslağı",
  CREATE_CAMPAIGN: "Kampanya taslağı",
  CREATE_EXPENSE: "Gider kaydı",
  REPLY_TO_REVIEW: "Yorum yanıtı",
  CREATE_SCHEDULE_BLOCK: "Takvim kapatma",
};

// Payload alanlarının ekranda görünen adları. Listede olmayan ve *_id ile biten alanlar gösterilmez.
const FIELD_LABELS: Record<string, string> = {
  customer_name: "Müşteri",
  appointment_date: "Tarih",
  start_time: "Başlangıç",
  end_time: "Bitiş",
  service_name: "Hizmet",
  notes: "Not",
  name: "Ad",
  target_segment: "Hedef kitle",
  offer: "Teklif",
  message: "Mesaj",
  start_date: "Başlangıç tarihi",
  end_date: "Bitiş tarihi",
  subtotal: "Ara toplam",
  tax_amount: "KDV",
  total_amount: "Toplam",
  due_date: "Son ödeme",
  title: "Başlık",
  amount: "Tutar",
  category_name: "Kategori",
  transaction_date: "Tarih",
  payment_method_label: "Ödeme yöntemi",
  description: "Açıklama",
  reviewer_name: "Yorum sahibi",
  rating: "Puan",
  review_comment: "Yorum",
  reply: "Yanıt",
  block_type_label: "Tür",
  branch_name: "Şube",
  recurrence_day_label: "Gün",
  reason: "Sebep",
  conflicting_appointments: "Çakışan randevu",
};

const MONEY_FIELDS = new Set(["subtotal", "tax_amount", "total_amount", "amount"]);
const LONG_FIELDS = new Set(["message", "reply", "review_comment", "description", "notes"]);

function formatValue(key: string, value: unknown): string {
  if (MONEY_FIELDS.has(key) && typeof value === "number") {
    return value.toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
  }
  if (key === "rating" && typeof value === "number") return `${"★".repeat(value)}${"☆".repeat(Math.max(0, 5 - value))}`;
  if (typeof value === "boolean") return value ? "Evet" : "Hayır";
  return String(value);
}

type ItemRow = { description?: string; quantity?: number; unit_price?: number; total?: number };

export type ActionOutcome = "approved" | "rejected";

interface PendingActionCardProps {
  action: PendingAgentAction;
  disabled?: boolean;
  outcome?: ActionOutcome;
  onApprove: (actionId: string) => void;
  onReject: (actionId: string, reason: string) => void;
}

export function PendingActionCard({ action, disabled, outcome, onApprove, onReject }: PendingActionCardProps) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const payload = action.payload ?? {};
  const title = ACTION_TITLES[action.action_type] ?? action.action_type;

  const fields = Object.entries(payload).filter(
    ([key, value]) => FIELD_LABELS[key] && value !== null && value !== undefined && value !== "",
  );
  const items = Array.isArray(payload.items) ? (payload.items as ItemRow[]) : [];

  if (outcome) {
    return (
      <div
        className={`mt-3 rounded-lg border p-3 text-xs ${
          outcome === "approved" ? "border-green-500/40 bg-green-50 text-green-900" : "border-border bg-surface text-ink-muted"
        }`}
      >
        <span className="font-semibold">{title}:</span> {outcome === "approved" ? "onaylandı ve uygulandı." : "reddedildi."}
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-amber-400/50 bg-amber-50 p-3 text-amber-950">
      <p className="text-xs font-semibold">Yönetici onayı bekleniyor · {title}</p>

      {fields.length > 0 && (
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
          {fields.map(([key, value]) => (
            <div key={key} className="contents">
              <dt className="text-amber-900/70">{FIELD_LABELS[key]}</dt>
              <dd className={LONG_FIELDS.has(key) ? "whitespace-pre-wrap font-medium" : "font-medium"}>
                {formatValue(key, value)}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {items.length > 0 && (
        <ul className="mt-2 space-y-0.5 border-t border-amber-400/40 pt-2 text-xs">
          {items.map((item, idx) => (
            <li key={idx} className="flex justify-between gap-3">
              <span>
                {item.quantity} × {item.description}
              </span>
              {typeof item.total === "number" && <span>{formatValue("amount", item.total)}</span>}
            </li>
          ))}
        </ul>
      )}

      <p className="mt-2 text-[11px] text-amber-900/70">Onaylandığında işlem tekrar doğrulanır ve uygulanır.</p>

      {rejecting ? (
        <form
          className="mt-2 flex flex-wrap items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            onReject(action.action_id, reason.trim() || "Kullanıcı tarafından reddedildi");
          }}
        >
          <Input
            autoFocus
            value={reason}
            maxLength={500}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reddetme sebebi (opsiyonel)"
            className="h-8 min-w-0 flex-1 bg-white text-xs"
          />
          <Button type="submit" size="sm" variant="outline" disabled={disabled}>
            Reddet
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={() => setRejecting(false)} disabled={disabled}>
            Vazgeç
          </Button>
        </form>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" className="gap-1.5" onClick={() => onApprove(action.action_id)} disabled={disabled}>
            <Check className="h-3.5 w-3.5" /> Onayla ve uygula
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setRejecting(true)} disabled={disabled}>
            <X className="h-3.5 w-3.5" /> Reddet
          </Button>
        </div>
      )}
    </div>
  );
}
