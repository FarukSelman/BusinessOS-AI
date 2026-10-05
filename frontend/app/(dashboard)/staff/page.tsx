"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, UserCog, Briefcase, Clock, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import {
  listStaff,
  createStaff,
  updateStaff,
  deleteStaff,
  listBranches,
  listServices,
  assignStaffServices,
  getStaffServices,
  setStaffSchedule,
  getStaffSchedule,
  type StaffProfile,
  type Branch,
  type BusinessService,
  type StaffScheduleItem
} from "@/lib/api";

const PREDEFINED_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#6366f1"
];

const DAYS_OF_WEEK = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"];

export default function StaffPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [staff, setStaff] = useState<StaffProfile[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [allServices, setAllServices] = useState<BusinessService[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [branchFilter, setBranchFilter] = useState<string>("ALL");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"PROFILE" | "SERVICES" | "SCHEDULE">("PROFILE");

  // Profile Form
  const [profileForm, setProfileForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    title: "",
    bio: "",
    branch_id: "",
    status: "ACTIVE",
    color: PREDEFINED_COLORS[0],
  });

  // Services Form
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  // Schedule Form
  const [scheduleForm, setScheduleForm] = useState<StaffScheduleItem[]>(
    DAYS_OF_WEEK.map((_, i) => ({ day_of_week: i, start_time: "09:00", end_time: "18:00", is_working: i < 5 }))
  );

  useEffect(() => {
    if (!businessId) return;
    Promise.all([
      loadStaff(),
      listBranches(businessId).then(setBranches),
      listServices(businessId).then(setAllServices)
    ]);
  }, [businessId, branchFilter]);

  async function loadStaff() {
    setLoading(true);
    try {
      const data = await listStaff(businessId!, branchFilter === "ALL" ? undefined : branchFilter);
      setStaff(data);
    } catch (err: any) {
      toast.error("Çalışanlar yüklenemedi: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleAdd() {
    setProfileForm({
      full_name: "",
      phone: "",
      email: "",
      title: "",
      bio: "",
      branch_id: branches.length > 0 ? branches[0].id : "",
      status: "ACTIVE",
      color: PREDEFINED_COLORS[Math.floor(Math.random() * PREDEFINED_COLORS.length)],
    });
    setSelectedServices([]);
    setScheduleForm(DAYS_OF_WEEK.map((_, i) => ({ day_of_week: i, start_time: "09:00", end_time: "18:00", is_working: i < 5 })));
    setEditingId(null);
    setActiveTab("PROFILE");
    setShowForm(true);
  }

  async function handleEdit(person: StaffProfile) {
    setProfileForm({
      full_name: person.full_name,
      phone: person.phone || "",
      email: person.email || "",
      title: person.title || "",
      bio: person.bio || "",
      branch_id: person.branch_id || (branches.length > 0 ? branches[0].id : ""),
      status: person.status,
      color: person.color || PREDEFINED_COLORS[0],
    });
    setEditingId(person.id);
    setActiveTab("PROFILE");
    setShowForm(true);
    
    // Load services & schedule
    try {
      const [srvs, sched] = await Promise.all([
        getStaffServices(businessId!, person.id),
        getStaffSchedule(businessId!, person.id)
      ]);
      setSelectedServices(srvs.map(s => s.id));
      if (sched && sched.length > 0) {
        setScheduleForm(sched);
      } else {
        setScheduleForm(DAYS_OF_WEEK.map((_, i) => ({ day_of_week: i, start_time: "09:00", end_time: "18:00", is_working: i < 5 })));
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete(id: string) {
    const ok = await confirmDialog({
      title: "Çalışanı Sil",
      description: "Bu çalışanı silmek istediğinize emin misiniz?",
      confirmLabel: "Sil",
      cancelLabel: "İptal",
    });
    if (!ok) return;

    try {
      await deleteStaff(businessId!, id);
      toast.success("Çalışan başarıyla silindi.");
      loadStaff();
    } catch (err: any) {
      toast.error("Çalışan silinemedi: " + err.message);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId) return;
    setSaving(true);
    try {
      let staffId = editingId;
      if (editingId) {
        await updateStaff(businessId, editingId, profileForm);
        toast.success("Çalışan bilgileri güncellendi.");
      } else {
        const newStaff = await createStaff(businessId, profileForm);
        staffId = newStaff.id;
        toast.success("Yeni çalışan eklendi.");
      }

      // Update services and schedule if editing existing or newly created
      if (staffId) {
        await assignStaffServices(businessId, staffId, selectedServices);
        await setStaffSchedule(businessId, staffId, scheduleForm);
      }

      setShowForm(false);
      loadStaff();
    } catch (err: any) {
      toast.error("İşlem başarısız: " + err.message);
    } finally {
      setSaving(false);
    }
  }

  function getInitials(name: string) {
    return name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
  }

  function toggleService(id: string) {
    if (selectedServices.includes(id)) {
      setSelectedServices(prev => prev.filter(s => s !== id));
    } else {
      setSelectedServices(prev => [...prev, id]);
    }
  }

  function updateSchedule(idx: number, field: keyof StaffScheduleItem, value: any) {
    setScheduleForm(prev => {
      const newSched = [...prev];
      newSched[idx] = { ...newSched[idx], [field]: value };
      return newSched;
    });
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[color-mix(in_srgb,var(--accent)_15%,transparent)]">
              <UserCog className="h-6 w-6" style={{ color: "var(--accent)" }} />
            </div>
            Çalışan Yönetimi
          </h1>
          <p className="mt-2 text-lg text-ink-muted">
            Personelinizi ve çalışma programlarını yönetin.
          </p>
        </div>
        {!showForm && (
          <div className="flex gap-4">
            <select
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={branchFilter}
              onChange={e => setBranchFilter(e.target.value)}
            >
              <option value="ALL">Tüm Şubeler</option>
              {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <Button onClick={handleAdd} className="gap-2 bg-accent text-white hover:bg-accent/90">
              <Plus className="h-4 w-4" />
              Yeni Çalışan Ekle
            </Button>
          </div>
        )}
      </div>

      {showForm ? (
        <Card className="border-border bg-surface shadow-sm">
          <CardHeader className="border-b border-border">
            <CardTitle>{editingId ? "Çalışanı Düzenle" : "Yeni Çalışan Ekle"}</CardTitle>
            <div className="flex gap-4 mt-4">
              <button 
                onClick={() => setActiveTab("PROFILE")}
                className={`pb-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "PROFILE" ? "border-accent text-accent" : "border-transparent text-ink-muted hover:text-ink"}`}
              >
                Profil Bilgileri
              </button>
              <button 
                onClick={() => setActiveTab("SERVICES")}
                className={`pb-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "SERVICES" ? "border-accent text-accent" : "border-transparent text-ink-muted hover:text-ink"}`}
              >
                Hizmetler
              </button>
              <button 
                onClick={() => setActiveTab("SCHEDULE")}
                className={`pb-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "SCHEDULE" ? "border-accent text-accent" : "border-transparent text-ink-muted hover:text-ink"}`}
              >
                Çalışma Saatleri
              </button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit}>
              
              {activeTab === "PROFILE" && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Ad Soyad</Label>
                    <Input required value={profileForm.full_name} onChange={e => setProfileForm({ ...profileForm, full_name: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Ünvan (Title)</Label>
                    <Input value={profileForm.title} onChange={e => setProfileForm({ ...profileForm, title: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Telefon</Label>
                    <Input value={profileForm.phone} onChange={e => setProfileForm({ ...profileForm, phone: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>E-posta</Label>
                    <Input type="email" value={profileForm.email} onChange={e => setProfileForm({ ...profileForm, email: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Şube</Label>
                    <select 
                      required
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={profileForm.branch_id}
                      onChange={e => setProfileForm({ ...profileForm, branch_id: e.target.value })}
                    >
                      <option value="" disabled>Seçiniz</option>
                      {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Durum</Label>
                    <select 
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={profileForm.status}
                      onChange={e => setProfileForm({ ...profileForm, status: e.target.value })}
                    >
                      <option value="ACTIVE">Aktif</option>
                      <option value="INACTIVE">Pasif</option>
                      <option value="ON_LEAVE">İzinde</option>
                    </select>
                  </div>
                  <div className="sm:col-span-2 space-y-2">
                    <Label>Biyografi / Notlar</Label>
                    <Input value={profileForm.bio} onChange={e => setProfileForm({ ...profileForm, bio: e.target.value })} />
                  </div>
                  <div className="sm:col-span-2 space-y-2">
                    <Label>Renk Etiketi</Label>
                    <div className="flex gap-2">
                      {PREDEFINED_COLORS.map(c => (
                        <div 
                          key={c}
                          onClick={() => setProfileForm({ ...profileForm, color: c })}
                          className={`w-8 h-8 rounded-full cursor-pointer flex items-center justify-center ${profileForm.color === c ? "ring-2 ring-offset-2 ring-accent" : ""}`}
                          style={{ backgroundColor: c }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "SERVICES" && (
                <div className="space-y-4">
                  <p className="text-sm text-ink-muted mb-4">Bu çalışanın sunabileceği hizmetleri seçin:</p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {allServices.length === 0 && (
                      <p className="text-sm text-ink-muted">Henüz hiç hizmet eklenmemiş.</p>
                    )}
                    {allServices.map(svc => (
                      <div key={svc.id} className="flex items-center space-x-3 p-3 border border-border rounded-lg bg-background">
                        <input
                          type="checkbox"
                          id={`svc-${svc.id}`}
                          className="h-4 w-4 rounded border-input"
                          checked={selectedServices.includes(svc.id)}
                          onChange={() => toggleService(svc.id)}
                        />
                        <label htmlFor={`svc-${svc.id}`} className="text-sm font-medium leading-none cursor-pointer flex-1">
                          {svc.name}
                          <div className="text-xs text-ink-muted mt-1">{svc.duration_minutes} dk</div>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === "SCHEDULE" && (
                <div className="space-y-4">
                  <p className="text-sm text-ink-muted mb-4">Çalışma saatlerini belirleyin:</p>
                  <div className="space-y-3">
                    {scheduleForm.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-4 p-3 border border-border rounded-lg bg-background">
                        <div className="w-24 text-sm font-medium">{DAYS_OF_WEEK[item.day_of_week]}</div>
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={item.is_working}
                            onChange={e => updateSchedule(idx, "is_working", e.target.checked)}
                            className="h-4 w-4 rounded border-input"
                          />
                          <span className="text-sm">Çalışıyor</span>
                        </div>
                        {item.is_working && (
                          <div className="flex items-center gap-2 ml-4">
                            <Input 
                              type="time" 
                              value={item.start_time}
                              onChange={e => updateSchedule(idx, "start_time", e.target.value)}
                              className="w-32"
                            />
                            <span className="text-muted-foreground">-</span>
                            <Input 
                              type="time" 
                              value={item.end_time}
                              onChange={e => updateSchedule(idx, "end_time", e.target.value)}
                              className="w-32"
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-6 mt-6 border-t border-border">
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            <div className="sm:col-span-3 text-center text-ink-muted py-8">Yükleniyor...</div>
          ) : staff.length === 0 ? (
            <div className="sm:col-span-3 text-center text-ink-muted py-8">
              Henüz hiç çalışan eklenmemiş.
            </div>
          ) : (
            staff.map((person) => (
              <Card key={person.id} className="border-border bg-surface shadow-sm relative overflow-hidden flex flex-col">
                <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: person.color }} />
                <CardContent className="p-5 flex-1 flex flex-col">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div 
                        className="h-10 w-10 rounded-full flex items-center justify-center text-white font-medium shadow-sm"
                        style={{ backgroundColor: person.color }}
                      >
                        {getInitials(person.full_name)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-ink">{person.full_name}</h3>
                        <p className="text-xs text-ink-muted">{person.title || "Çalışan"}</p>
                      </div>
                    </div>
                    {person.status !== "ACTIVE" && (
                      <span className="inline-flex items-center rounded-full bg-danger/10 px-2 py-0.5 text-[10px] font-medium text-danger">
                        {person.status === "INACTIVE" ? "Pasif" : "İzinde"}
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-4 space-y-2 text-sm text-ink-muted flex-1">
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      {branches.find(b => b.id === person.branch_id)?.name || "Şube atanmamış"}
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      {person.services?.length || 0} Hizmet Atalı
                    </div>
                  </div>
                  
                  <div className="flex gap-2 justify-end pt-4 mt-4 border-t border-border">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(person)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="text-danger hover:text-danger hover:bg-danger/10" onClick={() => handleDelete(person.id)}>
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
