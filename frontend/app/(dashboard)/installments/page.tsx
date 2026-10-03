"use client";

import { useEffect, useState } from "react";
import { CreditCard, AlertCircle, Clock, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listInstallments,
  payInstallment,
  listOverdueInstallments,
  ApiError,
  Installment
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

export default function InstallmentsPage() {
  const businessId = getActiveBusinessId();

  const [installments, setInstallments] = useState<Installment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [paying, setPaying] = useState<string | null>(null);

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      let data;
      if (statusFilter === "OVERDUE") {
        data = await listOverdueInstallments(businessId);
      } else {
        data = await listInstallments(businessId, { 
          status: statusFilter === "ALL" ? undefined : statusFilter 
        });
      }
      setInstallments(data);
    } catch (err) {
      toast.error("Taksitler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [businessId, statusFilter]);

  const handlePay = async (id: string) => {
    if (!businessId) return;
    setPaying(id);
    try {
      await payInstallment(businessId, id, { payment_method: "CREDIT_CARD" });
      toast.success("Taksit ödendi olarak işaretlendi.");
      refresh();
    } catch (err) {
      toast.error("İşlem başarısız.");
    } finally {
      setPaying(null);
    }
  };

  const overdueCount = installments.filter(i => i.status === "OVERDUE").length;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Taksit Takibi</h1>
          <p className="mt-1 text-sm text-ink-muted">Taksitli ödemeleri takip edin.</p>
        </div>
      </div>

      {statusFilter !== "OVERDUE" && overdueCount > 0 && (
        <Card className="bg-red-500/10 border-red-500/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">{overdueCount} adet gecikmiş taksit ödemesi bulunuyor.</span>
            </div>
            <Button size="sm" variant="outline" className="border-red-500/30 text-red-400 hover:bg-red-500/20" onClick={() => setStatusFilter("OVERDUE")}>
              Gecikmişleri Göster
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2">
        <Button variant={statusFilter === "ALL" ? "default" : "outline"} size="sm" onClick={() => setStatusFilter("ALL")}>Tümü</Button>
        <Button variant={statusFilter === "PENDING" ? "default" : "outline"} size="sm" onClick={() => setStatusFilter("PENDING")}>Bekleyen</Button>
        <Button variant={statusFilter === "PAID" ? "default" : "outline"} size="sm" onClick={() => setStatusFilter("PAID")}>Ödenen</Button>
        <Button variant={statusFilter === "OVERDUE" ? "default" : "outline"} size="sm" onClick={() => setStatusFilter("OVERDUE")}>Gecikmiş</Button>
      </div>

      {loading ? (
        <div className="text-center py-8 text-ink-muted flex items-center justify-center gap-2">
          <Clock className="animate-spin w-4 h-4"/> Yükleniyor...
        </div>
      ) : installments.length === 0 ? (
        <Card className="bg-surface-elevated border-border text-center py-12 text-ink-muted">
          <CreditCard className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Kayıt bulunamadı.</p>
        </Card>
      ) : (
        <Card className="bg-surface-elevated border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface text-ink-muted text-xs uppercase">
                <tr>
                  <th className="px-4 py-3">Müşteri</th>
                  <th className="px-4 py-3">Paket</th>
                  <th className="px-4 py-3 text-center">Taksit No</th>
                  <th className="px-4 py-3 text-right">Tutar</th>
                  <th className="px-4 py-3">Vade Tarihi</th>
                  <th className="px-4 py-3">Ödeme Tarihi</th>
                  <th className="px-4 py-3 text-center">Durum</th>
                  <th className="px-4 py-3 text-right">İşlem</th>
                </tr>
              </thead>
              <tbody>
                {installments.map((inst) => (
                  <tr key={inst.id} className={cn("border-t border-border hover:bg-white/[0.02]", inst.status === "OVERDUE" && "border-l-2 border-l-red-500")}>
                    <td className="px-4 py-3 text-ink font-medium">{inst.customer_name}</td>
                    <td className="px-4 py-3 text-ink-muted">{inst.package_name}</td>
                    <td className="px-4 py-3 text-center text-ink-muted font-medium">{inst.installment_number}</td>
                    <td className="px-4 py-3 text-right font-bold text-ink">{formatCurrency(inst.amount)}</td>
                    <td className={cn("px-4 py-3", inst.status === "OVERDUE" && "text-red-400 font-medium")}>{formatDate(inst.due_date)}</td>
                    <td className="px-4 py-3 text-ink-muted">{formatDate(inst.paid_date)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn(
                        "px-2 py-1 text-[10px] uppercase tracking-wider font-bold rounded-full",
                        inst.status === 'PAID' ? 'bg-emerald-500/15 text-emerald-400' : 
                        inst.status === 'PENDING' ? 'bg-yellow-500/15 text-yellow-400' : 
                        inst.status === 'OVERDUE' ? 'bg-red-500/15 text-red-400' : 
                        'bg-zinc-500/15 text-zinc-400'
                      )}>
                        {inst.status === 'PAID' ? 'Ödendi' : inst.status === 'PENDING' ? 'Bekliyor' : inst.status === 'OVERDUE' ? 'Gecikmiş' : 'İptal'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {(inst.status === 'PENDING' || inst.status === 'OVERDUE') && (
                        <Button 
                          size="sm" 
                          disabled={paying === inst.id}
                          onClick={() => handlePay(inst.id)}
                          style={{ backgroundColor: "var(--agent-finance)" }}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                          {paying === inst.id ? "..." : "Öde"}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
