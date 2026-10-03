"use client";

import { useEffect, useState } from "react";
import { Coins, Pencil, Plus, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getLoyaltyRules,
  updateLoyaltyRules,
  listLoyaltyWallets,
  earnPoints,
  spendPoints,
  adjustPoints,
  listLoyaltyTransactions,
  listCustomers,
  type LoyaltyRule,
  type LoyaltyWallet,
  type LoyaltyTransaction,
  type Customer,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

export default function LoyaltyPage() {
  const businessId = getActiveBusinessId();
  const confirmDialog = useConfirm();
  const [loading, setLoading] = useState(true);

  const [rules, setRules] = useState<LoyaltyRule | null>(null);
  const [wallets, setWallets] = useState<LoyaltyWallet[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [transactions, setTransactions] = useState<LoyaltyTransaction[]>([]);

  // Rules form
  const [isEditingRules, setIsEditingRules] = useState(false);
  const [ruleForm, setRuleForm] = useState<any>({});
  
  // Transaction form
  const [showTxForm, setShowTxForm] = useState<"EARN" | "SPEND" | "ADJUST" | null>(null);
  const [txForm, setTxForm] = useState({ customer_id: "", points: 0, description: "" });
  const [txSaving, setTxSaving] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    Promise.all([
      getLoyaltyRules(businessId).catch(() => null),
      listLoyaltyWallets(businessId).catch(() => []),
      listCustomers(businessId).catch(() => []),
      listLoyaltyTransactions(businessId).catch(() => []),
    ]).then(([r, w, c, t]) => {
      if (r) {
        setRules(r);
        setRuleForm({
          points_per_currency: r.points_per_currency,
          min_spend_for_earn: r.min_spend_for_earn,
          points_value_in_currency: r.points_value_in_currency,
          min_points_for_spend: r.min_points_for_spend,
          expiry_days: r.expiry_days || "",
          is_active: r.is_active,
        });
      }
      setWallets(w);
      setCustomers(c);
      setTransactions(t);
    }).finally(() => setLoading(false));
  }, [businessId]);

  async function handleSaveRules() {
    if (!businessId) return;
    try {
      const updated = await updateLoyaltyRules(businessId, {
        ...ruleForm,
        expiry_days: ruleForm.expiry_days ? Number(ruleForm.expiry_days) : null,
      });
      setRules(updated);
      setIsEditingRules(false);
      toast.success("Kurallar güncellendi");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Hata oluştu");
    }
  }

  async function handleTxSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId || !showTxForm) return;
    setTxSaving(true);
    try {
      if (showTxForm === "EARN") {
        await earnPoints(businessId, txForm);
      } else if (showTxForm === "SPEND") {
        await spendPoints(businessId, txForm);
      } else if (showTxForm === "ADJUST") {
        await adjustPoints(businessId, txForm);
      }
      toast.success("İşlem başarılı");
      setShowTxForm(null);
      setTxForm({ customer_id: "", points: 0, description: "" });
      
      // Refresh data
      const [w, t] = await Promise.all([
        listLoyaltyWallets(businessId),
        listLoyaltyTransactions(businessId),
      ]);
      setWallets(w);
      setTransactions(t);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem başarısız");
    } finally {
      setTxSaving(false);
    }
  }

  function getCustomerName(id: string) {
    return customers.find(c => c.id === id)?.name || "Bilinmiyor";
  }

  if (loading) return <div className="text-sm text-ink-muted">Yükleniyor...</div>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[color-mix(in_srgb,var(--agent-sales)_15%,transparent)]">
            <Coins className="h-5 w-5 text-[var(--agent-sales)]" />
          </div>
          <div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Parapuan Sistemi</h1>
            <p className="text-sm text-ink-muted">Sadakat programı kurallarını ve müşteri puanlarını yönet.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Kurallar</CardTitle>
            {!isEditingRules && (
              <Button variant="outline" size="sm" onClick={() => setIsEditingRules(true)}>
                Düzenle
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {isEditingRules ? (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Her 1 TL harcamaya kazanılacak puan</Label>
                    <Input type="number" step="0.01" value={ruleForm.points_per_currency} onChange={e => setRuleForm({ ...ruleForm, points_per_currency: Number(e.target.value) })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Minimum harcama tutarı (TL)</Label>
                    <Input type="number" value={ruleForm.min_spend_for_earn} onChange={e => setRuleForm({ ...ruleForm, min_spend_for_earn: Number(e.target.value) })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>1 puanın TL karşılığı</Label>
                    <Input type="number" step="0.01" value={ruleForm.points_value_in_currency} onChange={e => setRuleForm({ ...ruleForm, points_value_in_currency: Number(e.target.value) })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Harcama için min. puan</Label>
                    <Input type="number" value={ruleForm.min_points_for_spend} onChange={e => setRuleForm({ ...ruleForm, min_points_for_spend: Number(e.target.value) })} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Geçerlilik süresi (Gün - Boş bırakılabilir)</Label>
                    <Input type="number" value={ruleForm.expiry_days} onChange={e => setRuleForm({ ...ruleForm, expiry_days: e.target.value })} />
                  </div>
                  <div className="flex items-center gap-2 mt-6">
                    <input type="checkbox" checked={ruleForm.is_active} onChange={e => setRuleForm({ ...ruleForm, is_active: e.target.checked })} className="rounded border-gray-300" />
                    <Label>Sistem Aktif</Label>
                  </div>
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setIsEditingRules(false)}>Vazgeç</Button>
                  <Button onClick={handleSaveRules}>Kaydet</Button>
                </div>
              </div>
            ) : rules ? (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-ink-muted">Puan Kazanımı</p>
                  <p className="font-medium text-ink">1 TL = {rules.points_per_currency} Puan</p>
                </div>
                <div>
                  <p className="text-ink-muted">Min. Harcama</p>
                  <p className="font-medium text-ink">{rules.min_spend_for_earn} TL</p>
                </div>
                <div>
                  <p className="text-ink-muted">Puan Değeri</p>
                  <p className="font-medium text-ink">1 Puan = {rules.points_value_in_currency} TL</p>
                </div>
                <div>
                  <p className="text-ink-muted">Harcanabilir Min. Puan</p>
                  <p className="font-medium text-ink">{rules.min_points_for_spend} Puan</p>
                </div>
                <div>
                  <p className="text-ink-muted">Geçerlilik</p>
                  <p className="font-medium text-ink">{rules.expiry_days ? `${rules.expiry_days} Gün` : "Süresiz"}</p>
                </div>
                <div>
                  <p className="text-ink-muted">Durum</p>
                  <p className={cn("font-medium", rules.is_active ? "text-green-600" : "text-danger")}>
                    {rules.is_active ? "Aktif" : "Pasif"}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-ink-muted">Kural tanımlanmamış.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Manuel İşlemler</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1 text-green-600 hover:text-green-700" onClick={() => setShowTxForm("EARN")}>
                <Plus className="mr-2 h-4 w-4" /> Puan Ekle
              </Button>
              <Button variant="outline" className="flex-1 text-red-600 hover:text-red-700" onClick={() => setShowTxForm("SPEND")}>
                <Coins className="mr-2 h-4 w-4" /> Puan Harca
              </Button>
              <Button variant="outline" className="flex-1 text-yellow-600 hover:text-yellow-700" onClick={() => setShowTxForm("ADJUST")}>
                <Pencil className="mr-2 h-4 w-4" /> Düzeltme
              </Button>
            </div>
            
            {showTxForm && (
              <form onSubmit={handleTxSubmit} className="space-y-3 rounded-lg border p-4 bg-surface">
                <h4 className="font-medium">
                  {showTxForm === "EARN" ? "Puan Ekle" : showTxForm === "SPEND" ? "Puan Harca" : "Puan Düzeltme"}
                </h4>
                <div className="space-y-1.5">
                  <Label>Müşteri</Label>
                  <select
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={txForm.customer_id}
                    onChange={(e) => setTxForm({ ...txForm, customer_id: e.target.value })}
                    required
                  >
                    <option value="">Seçiniz</option>
                    {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label>Puan</Label>
                  <Input type="number" step="0.01" required value={txForm.points} onChange={e => setTxForm({ ...txForm, points: Number(e.target.value) })} />
                </div>
                <div className="space-y-1.5">
                  <Label>Açıklama</Label>
                  <Input required value={txForm.description} onChange={e => setTxForm({ ...txForm, description: e.target.value })} />
                </div>
                <div className="flex gap-2 pt-2">
                  <Button type="button" variant="ghost" onClick={() => setShowTxForm(null)}>İptal</Button>
                  <Button type="submit" disabled={txSaving}>Onayla</Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Müşteri Cüzdanları</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative w-full overflow-auto">
            <table className="w-full text-sm">
              <thead className="border-b text-left text-ink-muted">
                <tr>
                  <th className="pb-3 font-medium">Müşteri</th>
                  <th className="pb-3 font-medium">Mevcut Bakiye</th>
                  <th className="pb-3 font-medium">Toplam Kazanılan</th>
                  <th className="pb-3 font-medium">Toplam Harcanan</th>
                  <th className="pb-3 font-medium">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y text-ink">
                {wallets.length === 0 && <tr><td colSpan={5} className="py-4 text-center text-ink-muted">Cüzdan bulunamadı.</td></tr>}
                {wallets.map(w => (
                  <tr key={w.id} className="hover:bg-surface">
                    <td className="py-3">{getCustomerName(w.customer_id)}</td>
                    <td className="py-3 font-medium text-[var(--agent-sales)]">{w.balance}</td>
                    <td className="py-3 text-green-600">{w.lifetime_earned}</td>
                    <td className="py-3 text-red-600">{w.lifetime_spent}</td>
                    <td className="py-3">
                      <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", w.status === "ACTIVE" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700")}>
                        {w.status === "ACTIVE" ? "Aktif" : "Dondurulmuş"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Son İşlemler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {transactions.slice(0, 20).map(t => {
              const w = wallets.find(w => w.id === t.wallet_id);
              const cName = w ? getCustomerName(w.customer_id) : "Bilinmiyor";
              const typeColor = t.transaction_type === "EARN" || t.transaction_type === "BONUS" ? "text-green-600" : 
                               t.transaction_type === "SPEND" ? "text-red-600" : "text-yellow-600";
              const typeSign = t.transaction_type === "EARN" || t.transaction_type === "BONUS" || (t.transaction_type === "ADJUSTMENT" && t.points > 0) ? "+" : "";
              
              return (
                <div key={t.id} className="flex items-center justify-between border-b pb-3 last:border-0 last:pb-0">
                  <div>
                    <p className="font-medium text-ink">{cName}</p>
                    <p className="text-xs text-ink-muted">{t.description} • {new Date(t.created_at).toLocaleString("tr-TR")}</p>
                  </div>
                  <div className={cn("font-medium", typeColor)}>
                    {typeSign}{t.points}
                  </div>
                </div>
              );
            })}
            {transactions.length === 0 && <p className="text-sm text-ink-muted">İşlem geçmişi yok.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
