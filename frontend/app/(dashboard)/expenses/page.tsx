"use client";

import { useEffect, useState } from "react";
import { Plus, Wallet, Trash2, Pencil, CheckCircle2, Clock, Ban, PieChart, TrendingDown, TrendingUp, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listExpenses,
  createExpense,
  deleteExpense,
  getFinancialSummary,
  listExpenseCategories,
  ApiError,
  Expense,
  ExpenseCategory,
  FinancialSummary,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

export default function ExpensesPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [directionFilter, setDirectionFilter] = useState<"ALL" | "INCOME" | "EXPENSE">("ALL");

  // Form
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    direction: "EXPENSE" as "INCOME" | "EXPENSE",
    title: "",
    description: "",
    amount: 0,
    transaction_date: new Date().toISOString().split("T")[0],
    category_id: "",
    payment_method: "CASH",
    recurrence: "NONE",
  });

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    setError(null);
    
    // Get start/end of current month for summary
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];

    try {
      const [expResult, sumResult, catsResult] = await Promise.allSettled([
        listExpenses(businessId, { 
          direction: directionFilter === "ALL" ? undefined : directionFilter 
        }),
        getFinancialSummary(businessId, startOfMonth, endOfMonth),
        listExpenseCategories(businessId)
      ]);
      
      if (expResult.status === "fulfilled") setExpenses(expResult.value);
      if (sumResult.status === "fulfilled") setSummary(sumResult.value);
      if (catsResult.status === "fulfilled") setCategories(catsResult.value);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    refresh();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, directionFilter]);

  const handleCreate = async () => {
    if (!businessId) return;
    if (!form.title.trim() || form.amount <= 0) {
      toast.error("Başlık ve geçerli bir tutar girmelisiniz.");
      return;
    }

    setCreating(true);
    try {
      await createExpense(businessId, {
        direction: form.direction,
        title: form.title,
        description: form.description || null,
        amount: form.amount,
        currency: "TRY",
        transaction_date: form.transaction_date,
        category_id: form.category_id || null,
        payment_method: form.payment_method,
        recurrence: form.recurrence,
      });
      toast.success("İşlem başarıyla kaydedildi.");
      setShowCreate(false);
      setForm({
        direction: "EXPENSE",
        title: "",
        description: "",
        amount: 0,
        transaction_date: new Date().toISOString().split("T")[0],
        category_id: "",
        payment_method: "CASH",
        recurrence: "NONE",
      });
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem kaydedilemedi.");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "İşlemi Sil",
      description: "Bu işlemi silmek istediğinize emin misiniz?",
    });
    if (!ok) return;

    try {
      await deleteExpense(businessId, id);
      toast.success("İşlem silindi.");
      refresh();
    } catch (err) {
      toast.error("Silme başarısız.");
    }
  };

  if (error) {
    return <div className="flex items-center justify-center h-64 text-danger">{error}</div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Gelir-Gider Yönetimi</h1>
          <p className="mt-1 text-sm text-ink-muted">Tüm gelir ve giderlerinizi takip edin.</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2" style={{ backgroundColor: "var(--agent-finance)" }}>
          <Plus className="h-4 w-4" />
          {showCreate ? "Kapat" : "Yeni İşlem"}
        </Button>
      </div>

      {/* Summary Cards - calculated from loaded data */}
      {(() => {
        const totalIncome = expenses.filter(e => e.direction === "INCOME").reduce((s, e) => s + e.amount, 0);
        const totalExpense = expenses.filter(e => e.direction === "EXPENSE").reduce((s, e) => s + e.amount, 0);
        const netProfit = totalIncome - totalExpense;
        return (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-elevated border-border border-l-4 border-l-emerald-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><TrendingUp className="w-3 h-3 text-emerald-500"/> Toplam Gelir</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{formatCurrency(totalIncome)}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-red-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><TrendingDown className="w-3 h-3 text-red-500"/> Toplam Gider</p>
                <p className="text-xl font-bold text-red-400 mt-1">{formatCurrency(totalExpense)}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium">Net Kar</p>
                <p className={cn("text-xl font-bold mt-1", netProfit >= 0 ? "text-blue-400" : "text-red-400")}>{formatCurrency(netProfit)}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-violet-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium">Toplam İşlem</p>
                <p className="text-xl font-bold text-violet-400 mt-1">{expenses.length}</p>
              </CardContent>
            </Card>
          </div>
        );
      })()}

      {/* Create Form */}
      {showCreate && (
        <Card className="bg-surface-elevated border-border">
          <CardHeader>
            <CardTitle className="text-lg">Yeni Gelir/Gider Ekle</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Button 
                variant={form.direction === 'INCOME' ? 'default' : 'outline'} 
                className={cn("flex-1", form.direction === 'INCOME' && "bg-emerald-600 hover:bg-emerald-700")}
                onClick={() => setForm({...form, direction: 'INCOME'})}
              >Gelir</Button>
              <Button 
                variant={form.direction === 'EXPENSE' ? 'default' : 'outline'} 
                className={cn("flex-1", form.direction === 'EXPENSE' && "bg-red-600 hover:bg-red-700")}
                onClick={() => setForm({...form, direction: 'EXPENSE'})}
              >Gider</Button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Başlık *</Label>
                <Input value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="Örn: Ofis Kirası" />
              </div>
              <div className="space-y-1">
                <Label>Tutar (₺) *</Label>
                <Input type="number" min="0" step="0.01" value={form.amount || ''} onChange={e => setForm({...form, amount: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-1">
                <Label>Kategori</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={form.category_id}
                  onChange={e => setForm({...form, category_id: e.target.value})}
                >
                  <option value="">Kategori Seçin</option>
                  {categories.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Tarih *</Label>
                <Input type="date" value={form.transaction_date} onChange={e => setForm({...form, transaction_date: e.target.value})} />
              </div>
              <div className="space-y-1">
                <Label>Ödeme Yöntemi</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={form.payment_method}
                  onChange={e => setForm({...form, payment_method: e.target.value})}
                >
                  <option value="CASH">Nakit</option>
                  <option value="CREDIT_CARD">Kredi Kartı</option>
                  <option value="BANK_TRANSFER">Banka Transferi</option>
                  <option value="OTHER">Diğer</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label>Tekrar</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={form.recurrence}
                  onChange={e => setForm({...form, recurrence: e.target.value})}
                >
                  <option value="NONE">Tekrarsız</option>
                  <option value="DAILY">Günlük</option>
                  <option value="WEEKLY">Haftalık</option>
                  <option value="MONTHLY">Aylık</option>
                  <option value="YEARLY">Yıllık</option>
                </select>
              </div>
              <div className="space-y-1 md:col-span-2">
                <Label>Açıklama</Label>
                <Input value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="İsteğe bağlı açıklama..." />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={creating} className="gap-2" style={{ backgroundColor: "var(--agent-finance)" }}>
                <Wallet className="h-4 w-4" />
                {creating ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        <Button variant={directionFilter === "ALL" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("ALL")}>Tümü</Button>
        <Button variant={directionFilter === "INCOME" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("INCOME")}>Gelirler</Button>
        <Button variant={directionFilter === "EXPENSE" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("EXPENSE")}>Giderler</Button>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex justify-center p-8 text-ink-muted"><Clock className="animate-spin w-5 h-5 mr-2" /> Yükleniyor...</div>
      ) : expenses.length === 0 ? (
        <Card className="bg-surface-elevated border-border text-center py-12 text-ink-muted">
          <Wallet className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Kayıt bulunamadı.</p>
        </Card>
      ) : (
        <Card className="bg-surface-elevated border-border overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-surface text-ink-muted text-xs uppercase">
              <tr>
                <th className="px-4 py-3">Tarih</th>
                <th className="px-4 py-3">Başlık</th>
                <th className="px-4 py-3">Kategori</th>
                <th className="px-4 py-3 text-right">Tutar</th>
                <th className="px-4 py-3 text-center">Durum</th>
                <th className="px-4 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((exp) => (
                <tr key={exp.id} className="border-t border-border hover:bg-white/[0.02]">
                  <td className="px-4 py-3">{formatDate(exp.transaction_date)}</td>
                  <td className="px-4 py-3 text-ink font-medium">
                    {exp.title}
                    {exp.is_auto_generated && <span className="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">Otomatik</span>}
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {exp.category_name || "Kategorisiz"}
                  </td>
                  <td className={cn("px-4 py-3 text-right font-bold whitespace-nowrap", exp.direction === 'INCOME' ? 'text-emerald-400' : 'text-red-400')}>
                    {exp.direction === 'INCOME' ? '+' : '-'} {formatCurrency(exp.amount)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={cn(
                      "px-2 py-1 text-xs rounded-full inline-flex items-center gap-1",
                      exp.status === 'PAID' ? 'bg-emerald-500/15 text-emerald-400' : 
                      exp.status === 'PENDING' ? 'bg-yellow-500/15 text-yellow-400' : 
                      'bg-zinc-500/15 text-zinc-400'
                    )}>
                      {exp.status === 'PAID' ? 'Ödendi' : exp.status === 'PENDING' ? 'Bekliyor' : 'İptal'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(exp.id)}>
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
