"use client";

import React, { useEffect, useState } from "react";
import { Plus, Package, AlertTriangle, XCircle, Wallet, Pencil, Trash2, ChevronDown, ChevronRight, PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  getProductStockSummary,
  addProductStock,
  getProductMovements,
  ApiError,
  Product,
  StockSummary,
  StockMovement
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("tr-TR");
}

export default function ProductsPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [products, setProducts] = useState<Product[]>([]);
  const [summary, setSummary] = useState<StockSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  
  // Expanded & Forms
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [movements, setMovements] = useState<Record<string, StockMovement[]>>({});
  
  const [showCreate, setShowCreate] = useState(false);
  const [editProduct, setEditProduct] = useState<Product | null>(null);
  const [saving, setSaving] = useState(false);

  const [showStockForm, setShowStockForm] = useState<string | null>(null); // productId
  const [stockForm, setStockForm] = useState({ quantity: 0, movement_type: 'ADJUSTMENT', unit_price: 0, notes: '' });

  const initialForm = {
    name: "", description: "", sku: "", category: "", brand: "", unit: "Adet",
    purchase_price: 0, sale_price: 0, tax_rate: 20, min_stock_level: 0, max_stock_level: 0, status: "ACTIVE"
  };
  const [form, setForm] = useState(initialForm);

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      const [prodRes, sumRes] = await Promise.all([
        listProducts(businessId, { search, status: statusFilter, category: categoryFilter }),
        getProductStockSummary(businessId)
      ]);
      setProducts(prodRes);
      setSummary(sumRes);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (businessId) refresh();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId, search, statusFilter, categoryFilter]);

  const handleSave = async () => {
    if (!businessId) return;
    if (!form.name.trim()) { toast.error("Ürün adı gereklidir."); return; }
    
    setSaving(true);
    try {
      if (editProduct) {
        await updateProduct(businessId, editProduct.id, form);
        toast.success("Ürün güncellendi.");
      } else {
        await createProduct(businessId, form);
        toast.success("Ürün oluşturuldu.");
      }
      setShowCreate(false);
      setEditProduct(null);
      setForm(initialForm);
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem başarısız.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!businessId) return;
    const ok = await confirmDialog({ title: "Ürün Sil", description: "Bu ürünü silmek istediğinize emin misiniz?" });
    if (!ok) return;

    try {
      await deleteProduct(businessId, id);
      toast.success("Ürün silindi.");
      refresh();
    } catch (err) {
      toast.error("Silme başarısız.");
    }
  };

  const loadMovements = async (productId: string) => {
    if (!businessId) return;
    try {
      const res = await getProductMovements(businessId, productId);
      setMovements(prev => ({ ...prev, [productId]: res }));
    } catch (err) {
      toast.error("Stok hareketleri yüklenemedi.");
    }
  };

  const toggleRow = (productId: string) => {
    if (expandedRow === productId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(productId);
      if (!movements[productId]) loadMovements(productId);
    }
  };

  const handleAddStock = async (productId: string) => {
    if (!businessId) return;
    if (stockForm.quantity === 0) { toast.error("Miktar 0 olamaz."); return; }
    try {
      await addProductStock(businessId, productId, stockForm);
      toast.success("Stok güncellendi.");
      setShowStockForm(null);
      setStockForm({ quantity: 0, movement_type: 'ADJUSTMENT', unit_price: 0, notes: '' });
      loadMovements(productId);
      refresh();
    } catch (err) {
      toast.error("Stok güncellenemedi.");
    }
  };

  if (error) return <div className="p-6 text-danger">{error}</div>;

  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)));

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Ürün & Stok Yönetimi</h1>
          <p className="mt-1 text-sm text-ink-muted">Ürünlerinizi ve stok seviyelerinizi takip edin.</p>
        </div>
        <Button onClick={() => { setShowCreate(!showCreate); setEditProduct(null); setForm(initialForm); }} className="gap-2" style={{ backgroundColor: "var(--agent-sales)" }}>
          <Plus className="h-4 w-4" />
          {showCreate ? "Kapat" : "Yeni Ürün"}
        </Button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-surface-elevated border-border border-l-4" style={{ borderLeftColor: "var(--agent-sales)" }}>
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><Package className="w-3 h-3"/> Toplam Ürün</p>
              <p className="text-xl font-bold mt-1 text-ink">{summary.total_products}</p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border border-l-4 border-l-yellow-500">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-yellow-500"/> Düşük Stok</p>
              <p className="text-xl font-bold mt-1 text-yellow-500">{summary.low_stock_count}</p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border border-l-4 border-l-red-500">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><XCircle className="w-3 h-3 text-red-500"/> Stokta Yok</p>
              <p className="text-xl font-bold mt-1 text-red-500">{summary.out_of_stock_count}</p>
            </CardContent>
          </Card>
          <Card className="bg-surface-elevated border-border border-l-4 border-l-emerald-500">
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-ink-muted font-medium flex items-center gap-1"><Wallet className="w-3 h-3 text-emerald-500"/> Stok Değeri</p>
              <p className="text-xl font-bold mt-1 text-emerald-500">{formatCurrency(summary.total_stock_value)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {showCreate && (
        <Card className="bg-surface-elevated border-border">
          <CardHeader>
            <CardTitle className="text-lg">{editProduct ? "Ürünü Düzenle" : "Yeni Ürün Ekle"}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1"><Label>Ürün Adı *</Label><Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} /></div>
              <div className="space-y-1"><Label>SKU</Label><Input value={form.sku} onChange={e => setForm({...form, sku: e.target.value})} /></div>
              <div className="space-y-1"><Label>Kategori</Label><Input value={form.category} onChange={e => setForm({...form, category: e.target.value})} /></div>
              <div className="space-y-1"><Label>Marka</Label><Input value={form.brand} onChange={e => setForm({...form, brand: e.target.value})} /></div>
              <div className="space-y-1"><Label>Birim</Label>
                <select className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none" value={form.unit} onChange={e => setForm({...form, unit: e.target.value})}>
                  <option value="Adet">Adet</option><option value="Kg">Kg</option><option value="Lt">Lt</option><option value="Paket">Paket</option><option value="Kutu">Kutu</option>
                </select>
              </div>
              <div className="space-y-1"><Label>Durum</Label>
                <select className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none" value={form.status} onChange={e => setForm({...form, status: e.target.value})}>
                  <option value="ACTIVE">Aktif</option><option value="INACTIVE">Pasif</option><option value="OUT_OF_STOCK">Stokta Yok</option>
                </select>
              </div>
              <div className="space-y-1"><Label>Alış Fiyatı (₺)</Label><Input type="number" min="0" step="0.01" value={form.purchase_price} onChange={e => setForm({...form, purchase_price: parseFloat(e.target.value) || 0})} /></div>
              <div className="space-y-1"><Label>Satış Fiyatı (₺)</Label><Input type="number" min="0" step="0.01" value={form.sale_price} onChange={e => setForm({...form, sale_price: parseFloat(e.target.value) || 0})} /></div>
              <div className="space-y-1"><Label>KDV Oranı (%)</Label><Input type="number" min="0" step="1" value={form.tax_rate} onChange={e => setForm({...form, tax_rate: parseFloat(e.target.value) || 0})} /></div>
              <div className="space-y-1"><Label>Min. Stok Seviyesi</Label><Input type="number" min="0" value={form.min_stock_level} onChange={e => setForm({...form, min_stock_level: parseFloat(e.target.value) || 0})} /></div>
              <div className="space-y-1"><Label>Max. Stok Seviyesi</Label><Input type="number" min="0" value={form.max_stock_level} onChange={e => setForm({...form, max_stock_level: parseFloat(e.target.value) || 0})} /></div>
              <div className="space-y-1 md:col-span-3"><Label>Açıklama</Label><Input value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreate(false)}>İptal</Button>
              <Button onClick={handleSave} disabled={saving} style={{ backgroundColor: "var(--agent-sales)" }}>{saving ? "Kaydediliyor..." : "Kaydet"}</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-4">
        <Input placeholder="Ürün Ara (Ad, SKU)..." className="max-w-xs" value={search} onChange={e => setSearch(e.target.value)} />
        <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
          <option value="">Tüm Kategoriler</option>
          {categories.map(c => <option key={c as string} value={c as string}>{c as string}</option>)}
        </select>
        <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Tüm Durumlar</option>
          <option value="ACTIVE">Aktif</option>
          <option value="INACTIVE">Pasif</option>
          <option value="OUT_OF_STOCK">Stokta Yok</option>
        </select>
      </div>

      <Card className="bg-surface-elevated border-border overflow-hidden">
        {loading ? <div className="p-8 text-center text-ink-muted">Yükleniyor...</div> : products.length === 0 ? <div className="p-8 text-center text-ink-muted">Kayıt bulunamadı.</div> : (
          <table className="w-full text-sm text-left">
            <thead className="bg-surface text-ink-muted text-xs uppercase">
              <tr>
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3">Ürün Adı</th>
                <th className="px-4 py-3">SKU / Kategori</th>
                <th className="px-4 py-3 text-right">Alış / Satış</th>
                <th className="px-4 py-3 text-center">Stok</th>
                <th className="px-4 py-3 text-center">Durum</th>
                <th className="px-4 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {products.map(prod => {
                const isLowStock = prod.current_stock <= prod.min_stock_level && prod.current_stock > 0;
                const isOutOfStock = prod.current_stock === 0;
                return (
                  <React.Fragment key={prod.id}>
                    <tr className={cn("border-t border-border hover:bg-white/[0.02]", isLowStock && "border-l-4 border-l-amber-500", isOutOfStock && "border-l-4 border-l-red-500")}>
                      <td className="px-4 py-3 text-center">
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => toggleRow(prod.id)}>
                          {expandedRow === prod.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </Button>
                      </td>
                      <td className="px-4 py-3 font-medium text-ink">{prod.name}<br/><span className="text-xs text-ink-muted">{prod.brand || '-'}</span></td>
                      <td className="px-4 py-3 text-ink-muted">{prod.sku || '-'}<br/><span className="text-xs">{prod.category || 'Kategorisiz'}</span></td>
                      <td className="px-4 py-3 text-right text-ink-muted">{formatCurrency(prod.purchase_price)}<br/><span className="text-ink font-medium">{formatCurrency(prod.sale_price)}</span></td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn("px-2 py-1 text-xs rounded-full inline-flex font-bold", isOutOfStock ? "bg-red-500/15 text-red-500" : isLowStock ? "bg-amber-500/15 text-amber-500" : "bg-emerald-500/15 text-emerald-500")}>
                          {prod.current_stock} {prod.unit}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn("px-2 py-1 text-xs rounded-full", prod.status === 'ACTIVE' ? "bg-emerald-500/15 text-emerald-400" : prod.status === 'INACTIVE' ? "bg-zinc-500/15 text-zinc-400" : "bg-red-500/15 text-red-400")}>
                          {prod.status === 'ACTIVE' ? 'Aktif' : prod.status === 'INACTIVE' ? 'Pasif' : 'Yok'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right space-x-1">
                        <Button variant="ghost" size="icon" onClick={() => { setShowStockForm(showStockForm === prod.id ? null : prod.id); }} title="Stok Ekle"><PackagePlus className="h-4 w-4 text-emerald-500" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => { setEditProduct(prod); setForm(prod as any); setShowCreate(true); }}><Pencil className="h-4 w-4 text-ink-muted" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(prod.id)}><Trash2 className="h-4 w-4 text-danger" /></Button>
                      </td>
                    </tr>
                    
                    {showStockForm === prod.id && (
                      <tr className="border-b border-border bg-black/20">
                        <td colSpan={7} className="px-8 py-4">
                          <div className="flex items-end gap-4 p-4 border border-border rounded-lg bg-surface">
                            <div className="space-y-1"><Label>İşlem Tipi</Label>
                              <select className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none" value={stockForm.movement_type} onChange={e => setStockForm({...stockForm, movement_type: e.target.value})}>
                                <option value="ADJUSTMENT">Düzeltme</option><option value="PURCHASE">Alım</option><option value="RETURN">İade</option><option value="WASTE">Fire/Zayi</option>
                              </select>
                            </div>
                            <div className="space-y-1"><Label>Miktar (+ / -)</Label><Input type="number" value={stockForm.quantity} onChange={e => setStockForm({...stockForm, quantity: parseFloat(e.target.value) || 0})} /></div>
                            <div className="space-y-1"><Label>Birim Fiyat (Opsiyonel)</Label><Input type="number" min="0" step="0.01" value={stockForm.unit_price} onChange={e => setStockForm({...stockForm, unit_price: parseFloat(e.target.value) || 0})} /></div>
                            <div className="space-y-1 flex-1"><Label>Notlar</Label><Input value={stockForm.notes} onChange={e => setStockForm({...stockForm, notes: e.target.value})} placeholder="Açıklama..." /></div>
                            <Button onClick={() => handleAddStock(prod.id)} className="bg-emerald-600 hover:bg-emerald-700">Stok Güncelle</Button>
                          </div>
                        </td>
                      </tr>
                    )}

                    {expandedRow === prod.id && (
                      <tr className="border-b border-border bg-black/10">
                        <td colSpan={7} className="px-8 py-4">
                          <h4 className="text-sm font-semibold mb-2">Stok Hareketleri</h4>
                          {!movements[prod.id] ? <div className="text-xs text-ink-muted">Yükleniyor...</div> : movements[prod.id].length === 0 ? <div className="text-xs text-ink-muted">Hareket bulunamadı.</div> : (
                            <table className="w-full text-xs text-left">
                              <thead className="text-ink-muted border-b border-white/5">
                                <tr><th>Tarih</th><th>İşlem</th><th>Miktar</th><th>Birim Fiyat</th><th>Not</th></tr>
                              </thead>
                              <tbody>
                                {movements[prod.id].map(m => (
                                  <tr key={m.id} className="border-b border-white/5 last:border-0">
                                    <td className="py-2">{formatDate(m.created_at)}</td>
                                    <td className="py-2">{m.movement_type}</td>
                                    <td className={cn("py-2 font-bold", m.quantity > 0 ? "text-emerald-500" : "text-red-500")}>{m.quantity > 0 ? '+' : ''}{m.quantity}</td>
                                    <td className="py-2">{m.unit_price ? formatCurrency(m.unit_price) : '-'}</td>
                                    <td className="py-2 text-ink-muted">{m.notes || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
