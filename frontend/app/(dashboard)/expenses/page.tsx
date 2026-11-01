"use client";

import { Suspense, useEffect, useState } from "react";
import { Plus, Wallet, Trash2, Pencil, CheckCircle2, Clock, Ban, PieChart, TrendingDown, TrendingUp, Filter, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listExpensesPage,
  createExpense,
  deleteExpense,
  getFinancialSummary,
  listExpenseCategories,
  ApiError,
  Expense,
  ExpenseCategory,
  FinancialSummary,
} from "@/lib/api";
import { endOfMonth, startOfMonth } from "date-fns";
import { getActiveBusinessId } from "@/lib/business";
import { toISODate, todayISO } from "@/lib/date";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import { useListQuery } from "@/lib/use-list-query";
import { Pagination } from "@/components/ui/pagination";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

// useSearchParams (sayfa/arama URL'de) bir Suspense sınırı ister.
export default function ExpensesPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink-muted">Yükleniyor...</p>}>
      <ExpensesPageContent />
    </Suspense>
  );
}

const EXPENSE_FILTERS = ["direction"] as const;

function ExpensesPageContent() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  // Sayfa, arama (başlık/açıklama) ve gelir/gider filtresi backend'de; durum URL'de.
  const list = useListQuery<Expense>(
    EXPENSE_FILTERS,
    ({ page, search, filters, signal }) =>
      listExpensesPage(businessId!, { page, search, direction: filters.direction || undefined, signal }),
    !!businessId
  );
  const expenses = list.items;
  const directionFilter = (list.filters.direction || "ALL") as "ALL" | "INCOME" | "EXPENSE";
  const setDirectionFilter = (d: "ALL" | "INCOME" | "EXPENSE") => list.setFilter("direction", d === "ALL" ? "" : d);

  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Form
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    direction: "EXPENSE" as "INCOME" | "EXPENSE",
    title: "",
    description: "",
    amount: 0,
    transaction_date: todayISO(),
    category_id: "",
    payment_method: "CASH",
    recurrence: "NONE",
  });

  // Bu ayın özeti (kartlar) listeden bağımsız: filtre/arama/sayfa onu değiştirmez.
  const loadSummary = (id: string) => {
    const now = new Date();
    getFinancialSummary(id, toISODate(startOfMonth(now)), toISODate(endOfMonth(now)))
      .then(setSummary)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Özet yüklenemedi."));
  };

  /** Bir işlem eklenince/değişince listeyi (aynı sayfa) ve özeti yenile. */
  const refresh = () => {
    if (!businessId) return;
    list.reload();
    loadSummary(businessId);
  };

  useEffect(() => {
    if (!businessId) return;
    loadSummary(businessId);
    listExpenseCategories(businessId).then(setCategories).catch(() => setCategories([]));
  }, [businessId]);

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
        transaction_date: todayISO(),
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

  if (!businessId) {
    return <div className="flex items-center justify-center h-64 text-danger">Aktif işletme bulunamadı.</div>;
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

      {/* Özet kartları: bu ayın tüm işlemleri (backend özeti), listedeki ilk sayfa değil */}
      {(() => {
        const totalIncome = summary?.total_income ?? 0;
        const totalExpense = summary?.total_expense ?? 0;
        const netProfit = summary?.net_profit ?? 0;
        const show = (text: string) => (summary ? text : "—");
        return (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-elevated border-border border-l-4 border-l-emerald-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><TrendingUp className="w-3 h-3 text-emerald-500"/> Bu Ay Gelir</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{show(formatCurrency(totalIncome))}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-red-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><TrendingDown className="w-3 h-3 text-red-500"/> Bu Ay Gider</p>
                <p className="text-xl font-bold text-red-400 mt-1">{show(formatCurrency(totalExpense))}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium">Bu Ay Net Kâr</p>
                <p className={cn("text-xl font-bold mt-1", netProfit >= 0 ? "text-blue-400" : "text-red-400")}>{show(formatCurrency(netProfit))}</p>
              </CardContent>
            </Card>
            <Card className="bg-surface-elevated border-border border-l-4 border-l-violet-500">
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-ink-muted font-medium">Bu Ay İşlem</p>
                <p className="text-xl font-bold text-violet-400 mt-1">{show(String(summary?.transaction_count ?? 0))}</p>
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

      {(error || list.error) && <p className="text-sm text-danger">{error || list.error}</p>}

      {/* Search + Filter Tabs */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
        <Input
          className="pl-9"
          placeholder="Başlık veya açıklama..."
          value={list.searchInput}
          onChange={(e) => list.setSearchInput(e.target.value)}
          aria-label="İşlem ara"
        />
      </div>
      <div className="flex gap-2">
        <Button variant={directionFilter === "ALL" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("ALL")}>Tümü</Button>
        <Button variant={directionFilter === "INCOME" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("INCOME")}>Gelirler</Button>
        <Button variant={directionFilter === "EXPENSE" ? "default" : "outline"} size="sm" onClick={() => setDirectionFilter("EXPENSE")}>Giderler</Button>
      </div>

      {/* List */}
      {list.initialLoading ? (
        <div className="flex justify-center p-8 text-ink-muted"><Clock className="animate-spin w-5 h-5 mr-2" /> Yükleniyor...</div>
      ) : expenses.length === 0 && !list.loading && !list.error ? (
        <Card className="bg-surface-elevated border-border text-center py-12 text-ink-muted">
          <Wallet className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>
            {list.search || list.filters.direction
              ? `${list.search ? `"${list.search}" için ` : "Bu filtreyle "}sonuç yok — tüm işlemlerde arandı.`
              : "Kayıt bulunamadı."}
          </p>
        </Card>
      ) : (
        <>
        <Card className={cn("bg-surface-elevated border-border overflow-x-auto transition-opacity", list.loading && "opacity-60")} aria-busy={list.loading}>
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
        <Pagination page={list.page} pageCount={list.pageCount} total={list.total} loading={list.loading} onPageChange={list.setPage} />
        </>
      )}
    </div>
  );
}
