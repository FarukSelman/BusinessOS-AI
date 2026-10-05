"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Building2, Check, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import {
  listBranches,
  createBranch,
  updateBranch,
  deleteBranch,
  setMainBranch,
  type Branch
} from "@/lib/api";

const DAYS_OF_WEEK = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"];
const defaultWorkingHours = DAYS_OF_WEEK.reduce((acc, day, idx) => {
  acc[idx.toString()] = { open: "09:00", close: "18:00" };
  return acc;
}, {} as Record<string, { open: string; close: string }>);

type FormState = {
  name: string;
  address: string;
  phone: string;
  email: string;
  is_active: boolean;
  working_hours: Record<string, { open: string; close: string }>;
};

const emptyForm: FormState = {
  name: "",
  address: "",
  phone: "",
  email: "",
  is_active: true,
  working_hours: { ...defaultWorkingHours },
};

export default function BranchesPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();
  
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    loadBranches();
  }, [businessId]);

  async function loadBranches() {
    setLoading(true);
    try {
      const data = await listBranches(businessId!);
      setBranches(data);
    } catch (err: any) {
      toast.error("Şubeler yüklenemedi: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleAdd() {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(true);
  }

  function handleEdit(branch: Branch) {
    setForm({
      name: branch.name,
      address: branch.address || "",
      phone: branch.phone || "",
      email: branch.email || "",
      is_active: branch.is_active,
      working_hours: branch.working_hours || { ...defaultWorkingHours },
    });
    setEditingId(branch.id);
    setShowForm(true);
  }

  async function handleDelete(id: string) {
    const ok = await confirmDialog({
      title: "Şubeyi Sil",
      description: "Bu şubeyi silmek istediğinize emin misiniz? Bu işlem geri alınamaz.",
      confirmLabel: "Sil",
      cancelLabel: "İptal",
    });
    if (!ok) return;

    try {
      await deleteBranch(businessId!, id);
      toast.success("Şube başarıyla silindi.");
      loadBranches();
    } catch (err: any) {
      toast.error("Şube silinemedi: " + err.message);
    }
  }

  async function handleSetMain(id: string) {
    try {
      await setMainBranch(businessId!, id);
      toast.success("Ana şube olarak ayarlandı.");
      loadBranches();
    } catch (err: any) {
      toast.error("İşlem başarısız: " + err.message);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId) return;
    setSaving(true);
    try {
      if (editingId) {
        await updateBranch(businessId, editingId, form);
        toast.success("Şube güncellendi.");
      } else {
        await createBranch(businessId, form);
        toast.success("Yeni şube oluşturuldu.");
      }
      setShowForm(false);
      loadBranches();
    } catch (err: any) {
      toast.error("İşlem başarısız: " + err.message);
    } finally {
      setSaving(false);
    }
  }

  function updateWorkingHour(dayIdx: string, field: "open" | "close", value: string) {
    setForm(prev => ({
      ...prev,
      working_hours: {
        ...prev.working_hours,
        [dayIdx]: {
          ...prev.working_hours[dayIdx],
          [field]: value,
        }
      }
    }));
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[color-mix(in_srgb,var(--accent)_15%,transparent)]">
              <Building2 className="h-6 w-6" style={{ color: "var(--accent)" }} />
            </div>
            Şube Yönetimi
          </h1>
          <p className="mt-2 text-lg text-ink-muted">
            İşletmenizin şubelerini yönetin.
          </p>
        </div>
        {!showForm && (
          <Button onClick={handleAdd} className="gap-2 bg-accent text-white hover:bg-accent/90">
            <Plus className="h-4 w-4" />
            Yeni Şube Ekle
          </Button>
        )}
      </div>

      {showForm ? (
        <Card className="border-border bg-surface shadow-sm">
          <CardHeader>
            <CardTitle>{editingId ? "Şubeyi Düzenle" : "Yeni Şube Ekle"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Şube Adı</Label>
                  <Input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Telefon</Label>
                  <Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>E-posta</Label>
                  <Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Durum</Label>
                  <select 
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    value={form.is_active ? "true" : "false"}
                    onChange={e => setForm({ ...form, is_active: e.target.value === "true" })}
                  >
                    <option value="true">Aktif</option>
                    <option value="false">Pasif</option>
                  </select>
                </div>
                <div className="sm:col-span-2 space-y-2">
                  <Label>Adres</Label>
                  <Input value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} />
                </div>
              </div>

              <div>
                <h3 className="mb-4 text-sm font-medium">Çalışma Saatleri</h3>
                <div className="space-y-3">
                  {DAYS_OF_WEEK.map((day, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-24 text-sm font-medium">{day}</div>
                      <Input 
                        type="time" 
                        value={form.working_hours[idx.toString()]?.open || ""}
                        onChange={e => updateWorkingHour(idx.toString(), "open", e.target.value)}
                        className="w-32"
                      />
                      <span className="text-muted-foreground">-</span>
                      <Input 
                        type="time" 
                        value={form.working_hours[idx.toString()]?.close || ""}
                        onChange={e => updateWorkingHour(idx.toString(), "close", e.target.value)}
                        className="w-32"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-border">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  İptal
                </Button>
                <Button type="submit" disabled={saving} className="bg-accent text-white hover:bg-accent/90">
                  {saving ? "Kaydediliyor..." : "Kaydet"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {loading ? (
            <div className="sm:col-span-2 text-center text-ink-muted py-8">Yükleniyor...</div>
          ) : branches.length === 0 ? (
            <div className="sm:col-span-2 text-center text-ink-muted py-8">
              Henüz hiç şube eklenmemiş.
            </div>
          ) : (
            branches.map((branch) => (
              <Card key={branch.id} className="border-border bg-surface shadow-sm relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent" />
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {branch.name}
                        {branch.is_main && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600">
                            <Star className="h-3 w-3 fill-current" />
                            Ana Şube
                          </span>
                        )}
                        {!branch.is_active && (
                          <span className="inline-flex items-center rounded-full bg-danger/10 px-2 py-0.5 text-xs font-medium text-danger">
                            Pasif
                          </span>
                        )}
                      </CardTitle>
                      <CardDescription className="mt-1 line-clamp-1">{branch.address}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-ink-muted space-y-1 mb-4">
                    {branch.phone && <div>📞 {branch.phone}</div>}
                    {branch.email && <div>✉️ {branch.email}</div>}
                  </div>
                  
                  <div className="flex gap-2 justify-end pt-4 border-t border-border">
                    {!branch.is_main && branch.is_active && (
                      <Button variant="outline" size="sm" onClick={() => handleSetMain(branch.id)}>
                        Ana Şube Yap
                      </Button>
                    )}
                    <Button variant="outline" size="sm" onClick={() => handleEdit(branch)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="text-danger hover:text-danger hover:bg-danger/10" onClick={() => handleDelete(branch.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
