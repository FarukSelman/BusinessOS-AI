"use client";

import { useEffect, useState } from "react";
import {
  Plus,
  Receipt,
  CreditCard,
  Ban,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Send,
  FileText,
  Trash2,
  ChevronDown,
  ChevronUp,
  X,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listInvoices,
  createInvoice,
  markInvoicePaid,
  cancelInvoice,
  getRevenueStats,
  listCustomers,
  listServices,
  type Invoice,
  type InvoiceItem,
  type InvoiceStatus,
  type PaymentMethod,
  type RevenueStats,
  type Customer,
  type BusinessService,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import { exportToCSV } from "@/lib/export";

/* ---------- helpers ---------- */
const statusConfig: Record<InvoiceStatus, { label: string; color: string; icon: React.ElementType }> = {
  DRAFT: { label: "Taslak", color: "bg-gray-500/15 text-gray-400 border-gray-500/30", icon: FileText },
  SENT: { label: "Gönderildi", color: "bg-blue-500/15 text-blue-400 border-blue-500/30", icon: Send },
  PAID: { label: "Ödendi", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", icon: CheckCircle2 },
  OVERDUE: { label: "Gecikmiş", color: "bg-red-500/15 text-red-400 border-red-500/30", icon: AlertTriangle },
  CANCELLED: { label: "İptal", color: "bg-zinc-500/15 text-zinc-500 border-zinc-500/30", icon: Ban },
};

const paymentMethodLabels: Record<PaymentMethod, string> = {
  CASH: "Nakit",
  CREDIT_CARD: "Kredi Kartı",
  BANK_TRANSFER: "Banka Transferi",
  OTHER: "Diğer",
};

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

/* ---------- types ---------- */
type ItemRow = { description: string; quantity: number; unit_price: number };
const emptyItem: ItemRow = { description: "", quantity: 1, unit_price: 0 };

type CreateForm = {
  customer_name: string;
  customer_email: string;
  due_date: string;
  notes: string;
  tax_rate: number;
  items: ItemRow[];
};

const emptyForm: CreateForm = {
  customer_name: "",
  customer_email: "",
  due_date: "",
  notes: "",
  tax_rate: 0,
  items: [{ ...emptyItem }],
};

/* ---------- component ---------- */
export default function InvoicesPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<RevenueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<InvoiceStatus | "ALL">("ALL");

  /* create form */
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>({ ...emptyForm });
  const [creating, setCreating] = useState(false);

  /* lookups */
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<BusinessService[]>([]);

  /* expanded row */
  const [expandedId, setExpandedId] = useState<string | null>(null);

  /* pay modal */
  const [payingId, setPayingId] = useState<string | null>(null);
  const [payMethod, setPayMethod] = useState<PaymentMethod>("CASH");

  /* ---------- data fetching ---------- */
  function refresh() {
    if (!businessId) return;
    setLoading(true);
    Promise.all([
      listInvoices(businessId, filterStatus === "ALL" ? undefined : filterStatus),
      getRevenueStats(businessId),
    ])
      .then(([inv, st]) => {
        setInvoices(inv);
        setStats(st);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Faturalar yüklenemedi."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    refresh();
    // fetch lookups for form dropdowns
    listCustomers(businessId).then(setCustomers).catch(() => {});
    listServices(businessId).then(setServices).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, filterStatus]);

  /* ---------- form helpers ---------- */
  function updateItem(index: number, field: keyof ItemRow, value: string | number) {
    setForm((prev) => {
      const items = [...prev.items];
      items[index] = { ...items[index], [field]: value };
      return { ...prev, items };
    });
  }

  function addItem() {
    setForm((prev) => ({ ...prev, items: [...prev.items, { ...emptyItem }] }));
  }

  function removeItem(index: number) {
    setForm((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  }

  function calcSubtotal() {
    return form.items.reduce((sum, it) => sum + it.quantity * it.unit_price, 0);
  }

  function calcTax() {
    return calcSubtotal() * (form.tax_rate / 100);
  }

  function calcTotal() {
    return calcSubtotal() + calcTax();
  }

  /* ---------- create ---------- */
  async function handleCreate() {
    if (!businessId) return;
    if (!form.customer_name.trim()) {
      toast.error("Müşteri adı zorunludur.");
      return;
    }
    if (form.items.length === 0 || form.items.every((it) => !it.description.trim())) {
      toast.error("En az bir kalem ekleyin.");
      return;
    }

    setCreating(true);
    try {
      const subtotal = calcSubtotal();
      const tax_amount = calcTax();
      const total_amount = calcTotal();

      await createInvoice(businessId, {
        customer_name: form.customer_name.trim(),
        customer_email: form.customer_email.trim() || undefined,
        items: form.items.map((it) => ({
          description: it.description,
          quantity: it.quantity,
          unit_price: it.unit_price,
          total: it.quantity * it.unit_price,
        })),
        subtotal,
        tax_rate: form.tax_rate,
        tax_amount,
        total_amount,
        due_date: form.due_date || undefined,
        notes: form.notes.trim() || undefined,
      });

      toast.success("Fatura oluşturuldu.");
      setForm({ ...emptyForm, items: [{ ...emptyItem }] });
      setShowCreate(false);
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Fatura oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  /* ---------- actions ---------- */
  async function handlePay() {
    if (!businessId || !payingId) return;
    try {
      await markInvoicePaid(businessId, payingId, payMethod);
      toast.success("Fatura ödendi olarak işaretlendi.");
      setPayingId(null);
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem başarısız.");
    }
  }

  async function handleCancel(invoiceId: string) {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Faturayı İptal Et",
      description: "Bu faturayı iptal etmek istediğinize emin misiniz? Bu işlem geri alınamaz.",
    });
    if (!ok) return;
    try {
      await cancelInvoice(businessId, invoiceId);
      toast.success("Fatura iptal edildi.");
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İptal başarısız.");
    }
  }

  function handleExport() {
    const headers = ["Fatura No", "Müşteri", "Toplam", "Durum", "Oluşturma Tarihi", "Son Ödeme Tarihi"];
    const rows = invoices.map((inv) => [
      inv.invoice_number,
      inv.customer_name,
      inv.total_amount.toString(),
      statusConfig[inv.status].label,
      formatDate(inv.created_at),
      formatDate(inv.due_date),
    ]);
    exportToCSV("Faturalar", headers, rows);
  }

  /* ---------- render ---------- */
  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-danger">
        {error}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Faturalar</h1>
          <p className="mt-1 text-sm text-ink-muted">Fatura oluşturun, takip edin ve ödemeleri yönetin.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Dışa Aktar
          </Button>
          <Button onClick={() => setShowCreate(!showCreate)} className="gap-2">
            {showCreate ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            {showCreate ? "Kapat" : "Yeni Fatura"}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-surface-elevated border-border">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium">Toplam Gelir</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">{formatCurrency(stats.total_revenue)}</p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium">Ödenen</p>
              <p className="text-xl font-bold text-ink mt-1">{stats.paid_count} <span className="text-sm text-ink-muted font-normal">fatura</span></p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium">Bekleyen</p>
              <p className="text-xl font-bold text-amber-400 mt-1">{stats.pending_count} <span className="text-sm text-ink-muted font-normal">fatura</span></p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium">Gecikmiş</p>
              <p className="text-xl font-bold text-red-400 mt-1">{stats.overdue_count} <span className="text-sm text-ink-muted font-normal">fatura</span></p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <Card className="bg-surface-elevated border-border">
          <CardHeader>
            <CardTitle className="text-lg">Yeni Fatura Oluştur</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Customer */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Müşteri *</Label>
                <select
                  value=""
                  onChange={(e) => {
                    const c = customers.find((c) => c.id === e.target.value);
                    if (c) {
                      setForm({ ...form, customer_name: c.name, customer_email: c.email || "" });
                    }
                  }}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  <option value="" disabled>Listeden müşteri seçin...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}{c.email ? ` (${c.email})` : ''}</option>
                  ))}
                </select>
                <Input
                  value={form.customer_name}
                  onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                  placeholder="veya manuel girin"
                  className="mt-1"
                />
              </div>
              <div className="space-y-1">
                <Label>E-posta</Label>
                <Input
                  type="email"
                  value={form.customer_email}
                  onChange={(e) => setForm({ ...form, customer_email: e.target.value })}
                  placeholder="ornek@mail.com"
                />
              </div>
            </div>

            {/* Items */}
            <div className="space-y-2">
              <Label>Kalemler *</Label>
              {services.length > 0 && (
                <div className="flex items-center gap-2 mb-1">
                  <select
                    value=""
                    onChange={(e) => {
                      const s = services.find((s) => s.id === e.target.value);
                      if (s) {
                        setForm((prev) => ({
                          ...prev,
                          items: [...prev.items, { description: s.name, quantity: 1, unit_price: Number(s.price) }],
                        }));
                      }
                    }}
                    className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="" disabled>Hizmet listesinden ekle...</option>
                    {services.filter(s => s.status === 'ACTIVE').map((s) => (
                      <option key={s.id} value={s.id}>{s.name} — {formatCurrency(Number(s.price))}</option>
                    ))}
                  </select>
                </div>
              )}
              {form.items.map((item, i) => (
                <div key={i} className="flex items-end gap-2">
                  <div className="flex-1 space-y-1">
                    {i === 0 && <span className="text-xs text-ink-muted">Açıklama</span>}
                    <Input
                      value={item.description}
                      onChange={(e) => updateItem(i, "description", e.target.value)}
                      placeholder="Hizmet / ürün adı"
                    />
                  </div>
                  <div className="w-20 space-y-1">
                    {i === 0 && <span className="text-xs text-ink-muted">Adet</span>}
                    <Input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) => updateItem(i, "quantity", parseInt(e.target.value) || 1)}
                    />
                  </div>
                  <div className="w-28 space-y-1">
                    {i === 0 && <span className="text-xs text-ink-muted">Birim Fiyat</span>}
                    <Input
                      type="number"
                      min={0}
                      step={0.01}
                      value={item.unit_price}
                      onChange={(e) => updateItem(i, "unit_price", parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div className="w-24 text-right text-sm font-medium text-ink pt-1">
                    {i === 0 && <span className="block text-xs text-ink-muted mb-1">Toplam</span>}
                    {formatCurrency(item.quantity * item.unit_price)}
                  </div>
                  {form.items.length > 1 && (
                    <Button variant="ghost" size="icon" onClick={() => removeItem(i)} className="shrink-0">
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={addItem} className="gap-1 mt-1">
                <Plus className="h-3 w-3" /> Kalem Ekle
              </Button>
            </div>

            {/* Meta */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <Label>KDV Oranı (%)</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={form.tax_rate}
                  onChange={(e) => setForm({ ...form, tax_rate: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-1">
                <Label>Son Ödeme Tarihi</Label>
                <Input
                  type="date"
                  value={form.due_date}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Notlar</Label>
                <Input
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="İsteğe bağlı not"
                />
              </div>
            </div>

            {/* Totals */}
            <div className="flex justify-end">
              <div className="w-64 space-y-1 text-sm">
                <div className="flex justify-between text-ink-muted">
                  <span>Ara Toplam</span>
                  <span>{formatCurrency(calcSubtotal())}</span>
                </div>
                <div className="flex justify-between text-ink-muted">
                  <span>KDV ({form.tax_rate}%)</span>
                  <span>{formatCurrency(calcTax())}</span>
                </div>
                <div className="flex justify-between font-bold text-ink border-t border-border pt-1">
                  <span>Genel Toplam</span>
                  <span>{formatCurrency(calcTotal())}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={creating} className="gap-2">
                <Receipt className="h-4 w-4" />
                {creating ? "Oluşturuluyor..." : "Fatura Oluştur"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {(["ALL", "DRAFT", "SENT", "PAID", "OVERDUE", "CANCELLED"] as const).map((st) => (
          <Button
            key={st}
            variant={filterStatus === st ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterStatus(st)}
            className="text-xs"
          >
            {st === "ALL" ? "Tümü" : statusConfig[st].label}
          </Button>
        ))}
      </div>

      {/* Invoice List */}
      {loading ? (
        <div className="flex items-center justify-center h-32 text-ink-muted">
          <Clock className="h-5 w-5 animate-spin mr-2" /> Yükleniyor...
        </div>
      ) : invoices.length === 0 ? (
        <Card className="bg-surface-elevated border-border">
          <CardContent className="flex flex-col items-center justify-center py-12 text-ink-muted">
            <Receipt className="h-12 w-12 mb-3 opacity-40" />
            <p className="text-sm">Henüz fatura bulunmuyor.</p>
            <p className="text-xs mt-1">Yukarıdaki butona tıklayarak yeni bir fatura oluşturun.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {invoices.map((inv) => {
            const cfg = statusConfig[inv.status];
            const StatusIcon = cfg.icon;
            const isExpanded = expandedId === inv.id;
            return (
              <Card key={inv.id} className="bg-surface-elevated border-border overflow-hidden transition-all">
                {/* Main Row */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : inv.id)}
                  className="w-full flex items-center gap-4 p-4 text-left hover:bg-white/[0.02] transition-colors"
                >
                  <div className={cn("flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border", cfg.color)}>
                    <StatusIcon className="h-3 w-3" />
                    {cfg.label}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xs text-ink-muted">{inv.invoice_number}</span>
                      <span className="font-medium text-ink truncate">{inv.customer_name}</span>
                    </div>
                    <div className="text-xs text-ink-muted mt-0.5">
                      {formatDate(inv.created_at)}
                      {inv.due_date && <span className="ml-2">• Vade: {formatDate(inv.due_date)}</span>}
                    </div>
                  </div>
                  <span className="text-lg font-bold text-ink whitespace-nowrap">{formatCurrency(inv.total_amount)}</span>
                  {isExpanded ? <ChevronUp className="h-4 w-4 text-ink-muted" /> : <ChevronDown className="h-4 w-4 text-ink-muted" />}
                </button>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-border p-4 space-y-4 bg-surface/50">
                    {/* Items Table */}
                    <div>
                      <h4 className="text-xs font-semibold text-ink-muted uppercase tracking-wider mb-2">Kalemler</h4>
                      <div className="text-sm space-y-1">
                        <div className="grid grid-cols-12 gap-2 text-xs text-ink-muted font-medium pb-1 border-b border-border">
                          <span className="col-span-6">Açıklama</span>
                          <span className="col-span-2 text-right">Adet</span>
                          <span className="col-span-2 text-right">Birim Fiyat</span>
                          <span className="col-span-2 text-right">Toplam</span>
                        </div>
                        {inv.items.map((it, i) => (
                          <div key={i} className="grid grid-cols-12 gap-2 py-1">
                            <span className="col-span-6 text-ink">{it.description}</span>
                            <span className="col-span-2 text-right text-ink-muted">{it.quantity}</span>
                            <span className="col-span-2 text-right text-ink-muted">{formatCurrency(it.unit_price)}</span>
                            <span className="col-span-2 text-right font-medium text-ink">{formatCurrency(it.total)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Totals */}
                    <div className="flex justify-end">
                      <div className="w-56 space-y-1 text-sm">
                        <div className="flex justify-between text-ink-muted">
                          <span>Ara Toplam</span>
                          <span>{formatCurrency(inv.subtotal)}</span>
                        </div>
                        <div className="flex justify-between text-ink-muted">
                          <span>KDV ({inv.tax_rate}%)</span>
                          <span>{formatCurrency(inv.tax_amount)}</span>
                        </div>
                        <div className="flex justify-between font-bold text-ink border-t border-border pt-1">
                          <span>Toplam</span>
                          <span>{formatCurrency(inv.total_amount)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Meta */}
                    {(inv.customer_email || inv.notes || inv.payment_method || inv.paid_at) && (
                      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-muted border-t border-border pt-3">
                        {inv.customer_email && <span>📧 {inv.customer_email}</span>}
                        {inv.payment_method && <span>💳 {paymentMethodLabels[inv.payment_method]}</span>}
                        {inv.paid_at && <span>✅ Ödeme: {formatDate(inv.paid_at)}</span>}
                        {inv.notes && <span>📝 {inv.notes}</span>}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-2 border-t border-border">
                      {(inv.status === "DRAFT" || inv.status === "SENT" || inv.status === "OVERDUE") && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setPayingId(inv.id);
                            setPayMethod("CASH");
                          }}
                          className="gap-1"
                        >
                          <CreditCard className="h-3.5 w-3.5" />
                          Ödendi İşaretle
                        </Button>
                      )}
                      {(inv.status === "DRAFT" || inv.status === "SENT") && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleCancel(inv.id)}
                          className="gap-1 text-danger border-danger/30 hover:bg-danger/10"
                        >
                          <Ban className="h-3.5 w-3.5" />
                          İptal Et
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Pay Modal */}
      {payingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <Card className="w-full max-w-sm bg-surface-elevated border-border shadow-xl">
            <CardHeader>
              <CardTitle className="text-lg">Ödeme Yöntemi Seçin</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                {(Object.entries(paymentMethodLabels) as [PaymentMethod, string][]).map(([key, label]) => (
                  <Button
                    key={key}
                    variant={payMethod === key ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPayMethod(key)}
                    className="text-xs"
                  >
                    {label}
                  </Button>
                ))}
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={() => setPayingId(null)}>
                  Vazgeç
                </Button>
                <Button size="sm" onClick={handlePay} className="gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Onayla
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
