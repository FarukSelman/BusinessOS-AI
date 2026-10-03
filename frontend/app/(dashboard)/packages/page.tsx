"use client";

import { useEffect, useState } from "react";
import { Plus, Gift, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listPackages,
  createPackage,
  deletePackage,
  listServices,
  ApiError,
} from "@/lib/api";
import type { BusinessService } from "@/types";
import type { ServicePackage } from "@/types/packages";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

export default function PackagesPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [packages, setPackages] = useState<ServicePackage[]>([]);
  const [services, setServices] = useState<BusinessService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [form, setForm] = useState({
    name: "",
    description: "",
    price: 0,
    discount_percentage: 0,
    validity_days: 30,
    is_installment_allowed: false,
    max_installments: 1,
    services: [] as { service_id: string; session_count: number }[]
  });

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    setError(null);
    try {
      const [pkgs, srvs] = await Promise.all([
        listPackages(businessId),
        listServices(businessId)
      ]);
      setPackages(pkgs);
      setServices(srvs);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [businessId]);

  const handleAddService = () => {
    setForm(prev => ({
      ...prev,
      services: [...prev.services, { service_id: "", session_count: 1 }]
    }));
  };

  const handleUpdateService = (index: number, field: string, value: any) => {
    const newServices = [...form.services];
    newServices[index] = { ...newServices[index], [field]: value };
    setForm({ ...form, services: newServices });
  };

  const handleRemoveService = (index: number) => {
    setForm({ ...form, services: form.services.filter((_, i) => i !== index) });
  };

  const handleCreate = async () => {
    if (!businessId) return;
    if (!form.name.trim() || form.price <= 0 || form.services.length === 0) {
      toast.error("Paket adı, geçerli bir fiyat ve en az bir hizmet girmelisiniz.");
      return;
    }

    setCreating(true);
    try {
      // Backend requires service_name in each service item
      const payload = {
        ...form,
        services: form.services.map(s => {
          const svc = services.find(sv => sv.id === s.service_id);
          return { ...s, service_name: svc?.name || "" };
        })
      };
      await createPackage(businessId, payload);
      toast.success("Paket başarıyla oluşturuldu.");
      setShowCreate(false);
      setForm({
        name: "",
        description: "",
        price: 0,
        discount_percentage: 0,
        validity_days: 30,
        is_installment_allowed: false,
        max_installments: 1,
        services: []
      });
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Paket oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Paketi Sil",
      description: "Bu paketi silmek istediğinize emin misiniz? Önceden satılmış paketler etkilenmez.",
    });
    if (!ok) return;

    try {
      await deletePackage(businessId, id);
      toast.success("Paket silindi.");
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
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Paket Hizmetler</h1>
          <p className="mt-1 text-sm text-ink-muted">Hizmet paketlerinizi oluşturun ve müşterilere satın.</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2" style={{ backgroundColor: "var(--agent-appointments)" }}>
          <Plus className="h-4 w-4" />
          {showCreate ? "Kapat" : "Yeni Paket"}
        </Button>
      </div>

      {showCreate && (
        <Card className="bg-surface-elevated border-border">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><Gift className="w-5 h-5 text-accent"/> Yeni Paket Oluştur</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Paket Adı *</Label>
                <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Örn: 10 Seans Lazer Paketi" />
              </div>
              <div className="space-y-1">
                <Label>Açıklama</Label>
                <Input value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Kısa açıklama..." />
              </div>
              
              {/* Hizmetler */}
              <div className="md:col-span-2 p-4 border border-border rounded-md bg-surface space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Paket İçeriği (Hizmetler) *</Label>
                  <Button type="button" variant="outline" size="sm" onClick={handleAddService}>
                    <Plus className="w-4 h-4 mr-1"/> Hizmet Ekle
                  </Button>
                </div>
                {form.services.map((svc, idx) => (
                  <div key={idx} className="flex gap-2 items-center">
                    <select 
                      className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                      value={svc.service_id}
                      onChange={e => handleUpdateService(idx, 'service_id', e.target.value)}
                    >
                      <option value="">Hizmet Seçin</option>
                      {services.map(s => (
                        <option key={s.id} value={s.id}>{s.name} ({formatCurrency(s.price)})</option>
                      ))}
                    </select>
                    <Input 
                      type="number" min="1" className="w-24" placeholder="Seans" 
                      value={svc.session_count || ''} 
                      onChange={e => handleUpdateService(idx, 'session_count', parseInt(e.target.value) || 0)} 
                    />
                    <Button variant="ghost" size="icon" onClick={() => handleRemoveService(idx)}>
                      <Trash2 className="w-4 h-4 text-danger"/>
                    </Button>
                  </div>
                ))}
                {form.services.length === 0 && <p className="text-xs text-ink-muted text-center py-2">Henüz hizmet eklenmedi.</p>}
              </div>

              <div className="space-y-1">
                <Label>Fiyat (₺) *</Label>
                <Input type="number" min="0" value={form.price || ''} onChange={e => setForm({...form, price: parseFloat(e.target.value) || 0})} />
              </div>
              <div className="space-y-1">
                <Label>Geçerlilik Süresi (Gün)</Label>
                <Input type="number" min="1" value={form.validity_days || ''} onChange={e => setForm({...form, validity_days: parseInt(e.target.value) || 0})} />
              </div>
              
              <div className="space-y-1 border border-border rounded-md p-3">
                <div className="flex items-center justify-between mb-2">
                  <Label>Taksit İmkanı</Label>
                  <input type="checkbox" checked={form.is_installment_allowed} onChange={e => setForm({...form, is_installment_allowed: e.target.checked})} className="w-4 h-4 accent-blue-600"/>
                </div>
                {form.is_installment_allowed && (
                  <div>
                    <Label className="text-xs">Maksimum Taksit Sayısı</Label>
                    <Input type="number" min="1" max="12" value={form.max_installments || ''} onChange={e => setForm({...form, max_installments: parseInt(e.target.value) || 1})} />
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={creating} style={{ backgroundColor: "var(--agent-appointments)" }}>
                {creating ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading && packages.length === 0 ? (
        <div className="text-ink-muted flex justify-center py-8">Yükleniyor...</div>
      ) : packages.length === 0 ? (
        <Card className="bg-surface-elevated border-border text-center py-12 text-ink-muted">
          <Gift className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Henüz bir paket tanımlanmamış.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {packages.map(pkg => (
            <Card key={pkg.id} className="bg-surface-elevated border-border overflow-hidden flex flex-col">
              <div className="h-2 w-full" style={{ backgroundColor: "var(--agent-appointments)", opacity: 0.8 }} />
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{pkg.name}</CardTitle>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDelete(pkg.id)}>
                      <Trash2 className="h-3.5 w-3.5 text-danger" />
                    </Button>
                  </div>
                </div>
                <div className="text-2xl font-bold text-ink mt-2">{formatCurrency(pkg.price)}</div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-3">
                {pkg.description && <p className="text-sm text-ink-muted line-clamp-2">{pkg.description}</p>}
                
                <div className="space-y-1.5 mt-2">
                  <p className="text-xs font-semibold text-ink-muted uppercase">İçerik ({pkg.total_sessions} Seans)</p>
                  <div className="flex flex-wrap gap-1">
                    {pkg.services.map((s, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-ink">
                        {s.service_name} x{s.session_count}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-auto pt-4 flex items-center justify-between text-xs text-ink-muted">
                  <span>Süre: {pkg.validity_days} Gün</span>
                  {pkg.is_installment_allowed ? (
                    <span className="text-blue-400 bg-blue-400/10 px-2 py-1 rounded">Maks {pkg.max_installments} Taksit</span>
                  ) : (
                    <span className="text-ink-muted">Taksit Yok</span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
