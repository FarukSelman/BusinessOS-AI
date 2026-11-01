"use client";

import { Suspense, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Mail, Phone, Download, Sparkles, Filter, Tag as TagIcon, History, Coins, X, Check, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listCustomersPage,
  getCustomer,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  listCustomerTags,
  createCustomerTag,
  updateCustomerTag,
  deleteCustomerTag,
  assignTagToCustomer,
  removeTagFromCustomer,
  getCustomerHistory,
  getCustomerWallet,
  type Customer,
  type CustomerStatus,
  type CustomerTag,
  type CustomerTagBrief,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { fromISODate } from "@/lib/date";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import { useCsvExport } from "@/lib/use-csv-export";
import { useListQuery } from "@/lib/use-list-query";
import { useDeepLink } from "@/lib/use-deep-link";
import { Pagination } from "@/components/ui/pagination";

type FormState = {
  name: string;
  email: string;
  phone: string;
  notes: string;
};

const emptyForm: FormState = { name: "", email: "", phone: "", notes: "" };

// useSearchParams (sayfa/arama URL'de) bir Suspense sınırı ister.
export default function CustomersPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink-muted">Yükleniyor...</p>}>
      <CustomersPageContent />
    </Suspense>
  );
}

const CUSTOMER_FILTERS = ["status", "tags", "min_visits"] as const;

function CustomersPageContent() {
  const confirmDialog = useConfirm();
  const csvExport = useCsvExport();
  const businessId = getActiveBusinessId();

  const [error, setError] = useState<string | null>(null);

  // Sayfa, arama ve filtreler backend'de (tüm müşterilerde) çalışır; durum URL'de.
  const list = useListQuery<Customer>(
    CUSTOMER_FILTERS,
    ({ page, search, filters, signal }) =>
      listCustomersPage(businessId!, {
        page,
        search,
        status: filters.status,
        tagIds: filters.tags ? filters.tags.split(",") : undefined,
        minVisits: filters.min_visits || undefined,
        signal,
      }),
    !!businessId
  );
  const customers = list.items;
  const statusFilter = list.filters.status || "ALL";
  const selectedTagFilters = list.filters.tags ? list.filters.tags.split(",") : [];
  const setSelectedTagFilters = (ids: string[]) => list.setFilter("tags", ids.join(","));
  const filtersActive = !!(list.search || list.filters.status || list.filters.tags || list.filters.min_visits);

  // Data
  const [tags, setTags] = useState<CustomerTag[]>([]);
  // Etiket ata/kaldır sonrası listeyi yeniden çekmeden güncel göstermek için.
  const [tagOverrides, setTagOverrides] = useState<Record<string, CustomerTagBrief[]>>({});
  const tagsOf = (id: string) => tagOverrides[id] ?? customers.find((c) => c.id === id)?.tags ?? [];

  // Global aramadan gelen ?open=<id>: müşteri bu sayfada olmasa da detayını aç.
  useDeepLink(["open"], ({ open }) => {
    if (!businessId || !open) return;
    getCustomer(businessId, open)
      .then((c) => openCustomerDetail(c))
      .catch(() => toast.error("Müşteri bulunamadı."));
  });

  // Search & Filter
  const [showFilters, setShowFilters] = useState(false);

  // Forms
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<FormState>(emptyForm);
  const [creating, setCreating] = useState(false);

  // Editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<FormState>(emptyForm);
  const [savingEdit, setSavingEdit] = useState(false);

  // Tags Editor Modal
  const [showTagEditor, setShowTagEditor] = useState(false);
  const [tagForm, setTagForm] = useState({ name: "", color: "#3b82f6", description: "" });
  const [tagSaving, setTagSaving] = useState(false);

  // Customer Detail Drawer
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activeTab, setActiveTab] = useState<"SUMMARY" | "HISTORY" | "LOYALTY" | "TAGS">("SUMMARY");
  const [detailData, setDetailData] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    listCustomerTags(businessId)
      .then(setTags)
      .catch(() => setError("Veriler yüklenemedi."));
  }, [businessId]);


  // Ziyaret sayısı ve son ziyaret backend'den (müşterinin tüm randevuları üzerinden) gelir.
  function getInsight(customer: Customer) {
    const completed = customer.completed_visits ?? 0;
    const last = customer.last_visit_date;
    if (!last) return "Henüz randevu geçmişi yok. İlk ziyaret için hoş geldin kampanyası önerilebilir.";
    const daysSince = Math.floor((Date.now() - fromISODate(last).getTime()) / 86400000);
    if (daysSince > 60) return `${daysSince} gündür ziyaret etmedi. Yeniden kazanım kampanyası için uygun.`;
    return `${completed} tamamlanan randevu var. Son ziyaret: ${fromISODate(last).toLocaleDateString("tr-TR")}.`;
  }

  // --- Actions ---
  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId) return;
    setCreating(true);
    try {
      await createCustomer(businessId, { name: createForm.name, email: createForm.email || null, phone: createForm.phone || null, notes: createForm.notes || null });
      list.reload();
      setCreateForm(emptyForm);
      setShowCreateForm(false);
      toast.success("Müşteri eklendi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Eklenemedi.");
    } finally {
      setCreating(false);
    }
  }

  async function handleSaveEdit(id: string) {
    if (!businessId) return;
    setSavingEdit(true);
    try {
      await updateCustomer(businessId, id, { name: editForm.name, email: editForm.email || null, phone: editForm.phone || null, notes: editForm.notes || null });
      list.reload();
      setEditingId(null);
      toast.success("Güncellendi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Güncellenemedi.");
    } finally {
      setSavingEdit(false);
    }
  }

  async function toggleStatus(c: Customer) {
    if (!businessId) return;
    const next: CustomerStatus = c.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    try {
      await updateCustomer(businessId, c.id, { status: next });
      list.reload();
    } catch (err) {
      toast.error("Durum güncellenemedi.");
    }
  }

  async function handleDelete(id: string) {
    if (!businessId) return;
    const ok = await confirmDialog({ title: "Müşteriyi sil", description: "Emin misiniz?" });
    if (!ok) return;
    try {
      await deleteCustomer(businessId, id);
      list.reload();
      toast.success("Silindi.");
    } catch (err) {
      toast.error("Silinemedi.");
    }
  }

  // --- Tags ---
  async function handleCreateTag() {
    if (!businessId || !tagForm.name.trim()) return;
    setTagSaving(true);
    try {
      const nt = await createCustomerTag(businessId, tagForm);
      setTags([...tags, nt]);
      setTagForm({ name: "", color: "#3b82f6", description: "" });
      toast.success("Etiket eklendi.");
    } catch (err) {
      toast.error("Etiket eklenemedi.");
    } finally {
      setTagSaving(false);
    }
  }

  async function handleDeleteTag(id: string) {
    if (!businessId) return;
    try {
      await deleteCustomerTag(businessId, id);
      setTags(tags.filter(t => t.id !== id));
      toast.success("Etiket silindi.");
    } catch (err) {
      toast.error("Etiket silinemedi.");
    }
  }

  async function handleToggleCustomerTag(customerId: string, tagId: string, isAssigned: boolean) {
    if (!businessId) return;
    try {
      if (isAssigned) {
        await removeTagFromCustomer(businessId, customerId, tagId);
        setTagOverrides(prev => ({ ...prev, [customerId]: tagsOf(customerId).filter(t => t.id !== tagId) }));
      } else {
        await assignTagToCustomer(businessId, customerId, tagId);
        const addedTag = tags.find(t => t.id === tagId);
        if (addedTag) {
          setTagOverrides(prev => ({ ...prev, [customerId]: [...tagsOf(customerId), addedTag] }));
        }
      }
    } catch (err) {
      toast.error("Etiket güncellenemedi.");
    }
  }

  // --- Detail View ---
  async function openCustomerDetail(c: Customer) {
    setSelectedCustomer(c);
    setActiveTab("SUMMARY");
    setDetailLoading(true);
    try {
      const [hist, wall] = await Promise.all([
        getCustomerHistory(businessId!, c.id).catch(() => null),
        getCustomerWallet(businessId!, c.id).catch(() => null)
      ]);
      setDetailData({ history: hist, wallet: wall });
    } catch (err) {
      toast.error("Detaylar yüklenemedi");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Müşteriler</h1>
          <p className="text-sm text-ink-muted">İşletmenin müşteri kayıtlarını ve etiketlerini yönet.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" className="gap-2" onClick={() => setShowTagEditor(true)}>
            <TagIcon className="h-4 w-4" /> Etiketler
          </Button>
          <Button
            variant="outline"
            className="gap-2"
            disabled={csvExport.exporting || !businessId}
            onClick={() =>
              csvExport.run(
                "Musteriler",
                ["Ad", "Telefon"],
                (page, size) =>
                  listCustomersPage(businessId!, {
                    page,
                    size,
                    search: list.search,
                    status: list.filters.status,
                    tagIds: selectedTagFilters.length ? selectedTagFilters : undefined,
                    minVisits: list.filters.min_visits || undefined,
                  }).then((p) => p.items),
                (c) => [c.name, c.phone || ""]
              )
            }
          >
            <Download className="h-4 w-4" /> {csvExport.exporting ? "Hazırlanıyor..." : "Dışa Aktar"}
          </Button>
          {!showCreateForm && (
            <Button className="gap-2" onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4" /> Yeni müşteri
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex gap-2 w-full max-w-2xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-muted" />
            <Input className="pl-9" placeholder="İsim, telefon, e-posta..." value={list.searchInput} onChange={e => list.setSearchInput(e.target.value)} aria-label="Müşteri ara" />
          </div>
          <Button variant="outline" className={cn("gap-2", showFilters && "bg-surface")} onClick={() => setShowFilters(!showFilters)}>
            <Filter className="h-4 w-4" /> Filtreler
          </Button>
        </div>

        {showFilters && (
          <Card className="max-w-2xl bg-surface/50 border-dashed">
            <CardContent className="p-4 flex flex-col gap-4">
              <div className="flex gap-4 items-center">
                <Label className="w-20 shrink-0">Durum:</Label>
                <select className="text-sm rounded border px-2 py-1" value={statusFilter} onChange={e => list.setFilter("status", e.target.value === "ALL" ? "" : e.target.value)}>
                  <option value="ALL">Tümü</option>
                  <option value="ACTIVE">Aktif</option>
                  <option value="INACTIVE">Pasif</option>
                </select>
              </div>
              <div className="flex gap-4 items-center">
                <Label htmlFor="min-visits" className="w-20 shrink-0">Min. ziyaret:</Label>
                <Input
                  id="min-visits"
                  type="number"
                  min={1}
                  inputMode="numeric"
                  className="h-8 w-24"
                  placeholder="—"
                  value={list.filters.min_visits ?? ""}
                  onChange={(e) => {
                    const n = parseInt(e.target.value, 10);
                    list.setFilter("min_visits", n > 0 ? String(n) : "");
                  }}
                />
                <span className="text-xs text-ink-muted">tamamlanmış randevu</span>
              </div>
              <div className="flex gap-4 items-start">
                <Label className="w-20 shrink-0 mt-1">Etiketler:</Label>
                <div className="flex flex-wrap gap-2">
                  {tags.map(t => {
                    const isSelected = selectedTagFilters.includes(t.id);
                    return (
                      <button
                        key={t.id}
                        className={cn("px-2 py-1 rounded-full text-xs font-medium border flex items-center gap-1 transition-all", isSelected ? "opacity-100 ring-2 ring-offset-1" : "opacity-60")}
                        style={{ backgroundColor: `${t.color}20`, color: t.color, borderColor: `${t.color}40`, ...(isSelected && { ringColor: t.color }) }}
                        onClick={() => setSelectedTagFilters(isSelected ? selectedTagFilters.filter(x => x !== t.id) : [...selectedTagFilters, t.id])}
                      >
                        {isSelected && <Check className="h-3 w-3" />} {t.name}
                      </button>
                    )
                  })}
                  {tags.length === 0 && <span className="text-sm text-ink-muted">Etiket bulunamadı.</span>}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {!businessId && <p className="text-sm text-danger">Aktif işletme bulunamadı.</p>}
      {(error || list.error) && <p className="text-sm text-danger">{error || list.error}</p>}

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Yeni Müşteri Ekle</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5"><Label>Ad Soyad</Label><Input required value={createForm.name} onChange={e => setCreateForm({...createForm, name: e.target.value})} /></div>
              <div className="space-y-1.5"><Label>E-posta</Label><Input type="email" value={createForm.email} onChange={e => setCreateForm({...createForm, email: e.target.value})} /></div>
              <div className="space-y-1.5"><Label>Telefon</Label><Input value={createForm.phone} onChange={e => setCreateForm({...createForm, phone: e.target.value})} /></div>
              <div className="space-y-1.5 sm:col-span-2"><Label>Notlar</Label><Input value={createForm.notes} onChange={e => setCreateForm({...createForm, notes: e.target.value})} /></div>
              <div className="flex gap-2 sm:col-span-2">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowCreateForm(false)}>Vazgeç</Button>
                <Button type="submit" disabled={creating} className="flex-1">Ekle</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {list.initialLoading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : (
        <div className={cn("grid grid-cols-1 gap-4 transition-opacity", list.loading && "opacity-60")} aria-busy={list.loading}>
          {customers.map(c => (
            <Card key={c.id}>
              <CardContent className="p-4">
                {editingId === c.id ? (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <Input value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} placeholder="Ad Soyad" />
                    <Input value={editForm.email} onChange={e => setEditForm({...editForm, email: e.target.value})} placeholder="E-posta" />
                    <Input value={editForm.phone} onChange={e => setEditForm({...editForm, phone: e.target.value})} placeholder="Telefon" />
                    <Input value={editForm.notes} onChange={e => setEditForm({...editForm, notes: e.target.value})} placeholder="Notlar" />
                    <div className="flex gap-2 sm:col-span-2">
                      <Button variant="outline" className="flex-1" onClick={() => setEditingId(null)}>Vazgeç</Button>
                      <Button className="flex-1" disabled={savingEdit} onClick={() => handleSaveEdit(c.id)}>Kaydet</Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openCustomerDetail(c)} className="font-semibold text-lg hover:underline text-ink">{c.name}</button>
                        <button onClick={() => toggleStatus(c)} className={cn("rounded-full px-2 py-0.5 text-xs font-medium", c.status === "ACTIVE" ? "bg-success-soft text-success" : "bg-surface text-ink-muted")}>
                          {c.status === "ACTIVE" ? "Aktif" : "Pasif"}
                        </button>
                      </div>
                      
                      <div className="mt-1 flex flex-wrap gap-1">
                        {tagsOf(c.id).map(t => (
                          <span key={t.id} className="text-[10px] px-1.5 py-0.5 rounded border" style={{ backgroundColor: `${t.color}15`, color: t.color, borderColor: `${t.color}30` }}>
                            {t.name}
                          </span>
                        ))}
                      </div>

                      <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-ink-muted">
                        {c.email && <span className="flex items-center gap-1"><Mail className="h-3.5 w-3.5" /> {c.email}</span>}
                        {c.phone && <span className="flex items-center gap-1"><Phone className="h-3.5 w-3.5" /> {c.phone}</span>}
                      </div>
                      {c.notes && <p className="mt-1.5 text-sm text-ink-muted line-clamp-2">{c.notes}</p>}
                      <div className="mt-2 flex items-start gap-1.5 rounded-md bg-[color-mix(in_srgb,var(--agent-marketing)_8%,transparent)] px-2 py-1.5 text-xs text-ink-muted">
                        <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-[var(--agent-marketing)]" />
                        <span>{getInsight(c)}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-1 shrink-0">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingId(c.id); setEditForm({ name: c.name, email: c.email||"", phone: c.phone||"", notes: c.notes||"" }); }}>
                        <Pencil className="h-4 w-4 mr-1" /> Düzenle
                      </Button>
                      <Button variant="ghost" size="sm" className="text-danger hover:text-danger hover:bg-danger-soft" onClick={() => handleDelete(c.id)}>
                        <Trash2 className="h-4 w-4 mr-1" /> Sil
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {customers.length === 0 && !list.loading && !list.error && (
            <p className="text-sm text-ink-muted py-8 text-center border border-dashed rounded-lg">
              {filtersActive
                ? `${list.search ? `"${list.search}" için ` : "Bu filtrelerle "}sonuç yok — tüm müşterilerde arandı.`
                : "Henüz müşteri yok."}
            </p>
          )}
          {list.total > 0 && (
            <Pagination page={list.page} pageCount={list.pageCount} total={list.total} loading={list.loading} onPageChange={list.setPage} />
          )}
        </div>
      )}

      {/* Customer Detail Drawer/Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
            <CardHeader className="border-b pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-xl">{selectedCustomer.name}</CardTitle>
                <p className="text-sm text-ink-muted mt-1">{selectedCustomer.phone} • {selectedCustomer.email}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSelectedCustomer(null)}><X className="h-5 w-5" /></Button>
            </CardHeader>
            <div className="flex gap-4 px-6 pt-4 border-b">
              {[
                { id: "SUMMARY", label: "Özet" },
                { id: "HISTORY", label: "Geçmiş" },
                { id: "LOYALTY", label: "Puanlar" },
                { id: "TAGS", label: "Etiketler" }
              ].map(tab => (
                <button
                  key={tab.id}
                  className={cn("pb-2 text-sm font-medium border-b-2 transition-colors", activeTab === tab.id ? "border-[var(--accent)] text-[var(--accent)]" : "border-transparent text-ink-muted hover:text-ink")}
                  onClick={() => setActiveTab(tab.id as any)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <CardContent className="flex-1 overflow-auto p-6">
              {detailLoading ? (
                <p className="text-sm">Yükleniyor...</p>
              ) : activeTab === "SUMMARY" ? (
                <div className="space-y-4">
                  <div className="bg-[color-mix(in_srgb,var(--agent-marketing)_8%,transparent)] p-4 rounded-lg">
                    <h3 className="text-sm font-semibold text-[var(--agent-marketing)] flex items-center gap-1"><Sparkles className="h-4 w-4" /> AI Analizi</h3>
                    <p className="text-sm mt-2">{getInsight(selectedCustomer)}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="border p-3 rounded text-sm"><span className="text-ink-muted block">Kayıt Tarihi:</span> {new Date(selectedCustomer.created_at).toLocaleDateString("tr-TR")}</div>
                    <div className="border p-3 rounded text-sm"><span className="text-ink-muted block">Durum:</span> {selectedCustomer.status === "ACTIVE" ? "Aktif" : "Pasif"}</div>
                    <div className="border p-3 rounded text-sm col-span-2"><span className="text-ink-muted block">Notlar:</span> {selectedCustomer.notes || "-"}</div>
                  </div>
                </div>
              ) : activeTab === "HISTORY" ? (
                <div className="space-y-3">
                  {detailData?.history?.appointments?.length > 0 ? detailData.history.appointments.map((a: any) => (
                    <div key={a.id} className="border p-3 rounded text-sm flex justify-between items-center">
                      <div>
                        <span className="font-medium block">{fromISODate(a.appointment_date).toLocaleDateString("tr-TR")} {a.start_time}</span>
                        <span className="text-ink-muted text-xs">Durum: {a.status}</span>
                      </div>
                      <History className="h-4 w-4 text-ink-muted" />
                    </div>
                  )) : <p className="text-sm text-ink-muted">Geçmiş randevu yok.</p>}
                </div>
              ) : activeTab === "LOYALTY" ? (
                <div className="space-y-4">
                  {detailData?.wallet ? (
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-surface p-4 rounded-lg text-center"><span className="block text-xs text-ink-muted">Mevcut Bakiye</span><span className="text-xl font-bold text-success">{detailData.wallet.balance}</span></div>
                      <div className="bg-success-soft p-4 rounded-lg text-center"><span className="block text-xs text-success opacity-70">Kazanılan</span><span className="text-xl font-bold text-success">{detailData.wallet.lifetime_earned}</span></div>
                      <div className="bg-danger-soft p-4 rounded-lg text-center"><span className="block text-xs text-danger opacity-70">Harcanan</span><span className="text-xl font-bold text-danger">{detailData.wallet.lifetime_spent}</span></div>
                    </div>
                  ) : <p className="text-sm text-ink-muted">Parapuan cüzdanı bulunamadı.</p>}
                </div>
              ) : activeTab === "TAGS" ? (
                <div className="space-y-4">
                  <p className="text-sm mb-2 font-medium">Bu müşteriye ait etiketler:</p>
                  <div className="flex flex-col gap-2">
                    {tags.map(t => {
                      const cTags = tagsOf(selectedCustomer.id);
                      const isAssigned = cTags.some(x => x.id === t.id);
                      return (
                        <div key={t.id} className="flex items-center justify-between p-2 border rounded hover:bg-surface">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: t.color }} />
                            <span className="text-sm font-medium">{t.name}</span>
                          </div>
                          <Button size="sm" variant={isAssigned ? "destructive" : "outline"} className={isAssigned ? "bg-danger-soft text-danger hover:bg-danger-soft border-danger-border" : ""} onClick={() => handleToggleCustomerTag(selectedCustomer.id, t.id, isAssigned)}>
                            {isAssigned ? "Kaldır" : "Ekle"}
                          </Button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tag Editor Modal */}
      {showTagEditor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-md shadow-xl">
            <CardHeader className="flex flex-row justify-between items-center border-b pb-4">
              <CardTitle className="text-lg">Etiket Yönetimi</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setShowTagEditor(false)}><X className="h-4 w-4" /></Button>
            </CardHeader>
            <CardContent className="p-4 space-y-6">
              <form onSubmit={e => { e.preventDefault(); handleCreateTag(); }} className="space-y-3">
                <div className="space-y-1.5"><Label>Yeni Etiket Adı</Label><Input required value={tagForm.name} onChange={e => setTagForm({...tagForm, name: e.target.value})} /></div>
                <div className="space-y-1.5">
                  <Label>Renk Seç</Label>
                  <div className="flex gap-2">
                    {["#ef4444", "#f97316", "#f59e0b", "#10b981", "#3b82f6", "#6366f1", "#8b5cf6", "#ec4899", "#64748b"].map(c => (
                      <button key={c} type="button" className={cn("w-6 h-6 rounded-full cursor-pointer ring-offset-2", tagForm.color === c && "ring-2 ring-border")} style={{ backgroundColor: c }} onClick={() => setTagForm({...tagForm, color: c})} />
                    ))}
                  </div>
                </div>
                <Button type="submit" className="w-full mt-2" disabled={tagSaving}>Oluştur</Button>
              </form>
              
              <div className="space-y-2 border-t pt-4">
                <Label className="text-xs uppercase text-ink-muted">Mevcut Etiketler</Label>
                {tags.map(t => (
                  <div key={t.id} className="flex justify-between items-center text-sm p-2 bg-surface rounded">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: t.color }} />
                      <span className="font-medium">{t.name}</span>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-danger" onClick={() => handleDeleteTag(t.id)}><Trash2 className="h-3 w-3" /></Button>
                  </div>
                ))}
                {tags.length === 0 && <p className="text-xs text-ink-muted">Henüz etiket yok.</p>}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

    </div>
  );
}
