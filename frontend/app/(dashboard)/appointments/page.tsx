"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Clock, User as UserIcon, Phone, Check, X, Pencil, List, Calendar as CalendarIcon, Download, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listAppointmentsByDate,
  listAppointments,
  createAppointment,
  updateAppointment,
  cancelAppointment,
  completeAppointment,
  getAvailableSlots,
  listCustomers,
  listServices,
  type Appointment,
  type AppointmentStatus,
  type Customer,
  type BusinessService,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import { exportToCSV } from "@/lib/export";

const statusStyles: Record<AppointmentStatus, { label: string; color: string }> = {
  PENDING: { label: "Beklemede", color: "var(--agent-appointments)" },
  CONFIRMED: { label: "Onaylandı", color: "var(--agent-sales)" },
  CANCELLED: { label: "İptal edildi", color: "var(--danger)" },
  COMPLETED: { label: "Tamamlandı", color: "var(--ink-muted)" },
  NO_SHOW: { label: "Gelmedi", color: "var(--agent-marketing)" },
};

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

type FormState = {
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  service_id: string;
  start_time: string;
  end_time: string;
  notes: string;
};

const emptyForm: FormState = {
  customer_id: "",
  customer_name: "",
  customer_phone: "",
  customer_email: "",
  service_id: "",
  start_time: "",
  end_time: "",
  notes: "",
};

export default function AppointmentsPage() {
  const confirmDialog = useConfirm();
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "ALL">("ALL");
  const businessId = getActiveBusinessId();

  const [viewMode, setViewMode] = useState<"LIST" | "CALENDAR">("LIST");
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
  });
  const [monthAppointments, setMonthAppointments] = useState<Appointment[]>([]);

  const [selectedDate, setSelectedDate] = useState(todayISO());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<BusinessService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<FormState>(emptyForm);
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<FormState>(emptyForm);
  const [savingEdit, setSavingEdit] = useState(false);

  // Müşteri ve hizmet listeleri (dropdown için) - bir kez, tarih değişse de yeniden çekilmesine gerek yok
  useEffect(() => {
    if (!businessId) return;
    listCustomers(businessId).then(setCustomers).catch(() => setCustomers([]));
    listServices(businessId).then(setServices).catch(() => setServices([]));
  }, [businessId]);

  useEffect(() => {
    if (viewMode === "CALENDAR" && businessId) {
      listAppointments(businessId, 1, 1000).then(setMonthAppointments).catch(console.error);
    }
  }, [viewMode, calendarMonth, businessId]);

  function handleExport() {
    if (!businessId) return;
    listAppointments(businessId, 1, 1000).then((res) => {
      const headers = ["Müşteri", "Hizmet", "Tarih", "Saat", "Durum", "Notlar"];
      const rows = res.map((a) => [
        a.customer_name,
        services.find((s) => s.id === a.service_id)?.name || "",
        a.appointment_date,
        a.start_time,
        statusStyles[a.status].label,
        a.notes || "",
      ]);
      exportToCSV("Randevular", headers, rows);
    });
  }

  const loadData = useCallback(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      listAppointmentsByDate(businessId, selectedDate),
      getAvailableSlots(businessId, selectedDate).catch(() => ({ date: selectedDate, available_slots: [] })),
    ])
      .then(([appts, slotData]) => {
        setAppointments(appts);
        setSlots(slotData.available_slots);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Randevular yüklenemedi."))
      .finally(() => setLoading(false));
  }, [businessId, selectedDate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredAppointments = appointments.filter((a) =>
    statusFilter === "ALL" ? true : a.status === statusFilter
  );

  function toHms(t: string) {
    // <input type="time"> "HH:MM" döndürür, backend "HH:MM:SS" bekliyor
    return t.length === 5 ? `${t}:00` : t;
  }

  function toHm(t: string) {
    return t.slice(0, 5);
  }

  function addMinutes(hm: string, minutes: number) {
    const [h, m] = hm.split(":").map(Number);
    const total = h * 60 + m + minutes;
    const nh = Math.floor(total / 60) % 24;
    const nm = total % 60;
    return `${String(nh).padStart(2, "0")}:${String(nm).padStart(2, "0")}`;
  }

  function applyCustomerSelection(
    customerId: string,
    setForm: React.Dispatch<React.SetStateAction<FormState>>
  ) {
    const customer = customers.find((c) => c.id === customerId);
    setForm((f) => ({
      ...f,
      customer_id: customerId,
      customer_name: customer ? customer.name : f.customer_name,
      customer_phone: customer?.phone ?? f.customer_phone,
      customer_email: customer?.email ?? f.customer_email,
    }));
  }

  function applyServiceSelection(
    serviceId: string,
    setForm: React.Dispatch<React.SetStateAction<FormState>>
  ) {
    const service = services.find((s) => s.id === serviceId);
    setForm((f) => ({
      ...f,
      service_id: serviceId,
      end_time:
        service?.duration_minutes && f.start_time
          ? addMinutes(f.start_time, service.duration_minutes)
          : f.end_time,
    }));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId) return;
    setCreating(true);
    setError(null);
    try {
      await createAppointment(businessId, {
        customer_name: createForm.customer_name,
        customer_phone: createForm.customer_phone || null,
        customer_email: createForm.customer_email || null,
        customer_id: createForm.customer_id || null,
        service_id: createForm.service_id || null,
        appointment_date: selectedDate,
        start_time: toHms(createForm.start_time),
        end_time: createForm.end_time ? toHms(createForm.end_time) : null,
        notes: createForm.notes || null,
      });
      setCreateForm(emptyForm);
      setShowCreateForm(false);
      toast.success("Randevu oluşturuldu.");
      loadData();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Randevu oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(a: Appointment) {
    setEditingId(a.id);
    setEditForm({
      customer_id: a.customer_id ?? "",
      customer_name: a.customer_name,
      customer_phone: a.customer_phone ?? "",
      customer_email: a.customer_email ?? "",
      service_id: a.service_id ?? "",
      start_time: toHm(a.start_time),
      end_time: a.end_time ? toHm(a.end_time) : "",
      notes: a.notes ?? "",
    });
  }

  async function handleSaveEdit(appointmentId: string) {
    if (!businessId) return;
    setSavingEdit(true);
    setError(null);
    try {
      await updateAppointment(businessId, appointmentId, {
        customer_name: editForm.customer_name,
        customer_phone: editForm.customer_phone || null,
        customer_email: editForm.customer_email || null,
        customer_id: editForm.customer_id || null,
        service_id: editForm.service_id || null,
        start_time: toHms(editForm.start_time),
        end_time: editForm.end_time ? toHms(editForm.end_time) : null,
        notes: editForm.notes || null,
      });
      setEditingId(null);
      toast.success("Güncellendi.");
      loadData();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Güncellenemedi.");
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleCancel(appointmentId: string) {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Randevuyu iptal et",
      description: "Bu randevuyu iptal etmek istediğine emin misin?",
    });
    if (!ok) return;
    try {
      await cancelAppointment(businessId, appointmentId);
      loadData();
      toast.success("Randevu iptal edildi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İptal edilemedi.");
    }
  }

  async function handleComplete(appointmentId: string) {
    if (!businessId) return;
    try {
      await completeAppointment(businessId, appointmentId);
      loadData();
      toast.success("Randevu tamamlandı.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Tamamlanamadı.");
    }
  }

  function renderCalendar() {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(year, month, 1).getDay();
    const firstDayNormalized = firstDay === 0 ? 6 : firstDay - 1; // Mon = 0

    const appsByDate = monthAppointments.reduce((acc, appt) => {
      if (!acc[appt.appointment_date]) acc[appt.appointment_date] = [];
      acc[appt.appointment_date].push(appt);
      return acc;
    }, {} as Record<string, Appointment[]>);

    const prevMonth = () => setCalendarMonth(new Date(year, month - 1, 1));
    const nextMonth = () => setCalendarMonth(new Date(year, month + 1, 1));

    const monthNames = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];

    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">{monthNames[month]} {year}</h2>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={prevMonth}><ChevronLeft className="h-4 w-4" /></Button>
            <Button variant="outline" size="icon" onClick={nextMonth}><ChevronRight className="h-4 w-4" /></Button>
          </div>
        </div>
        <div className="grid grid-cols-7 gap-px bg-border rounded-lg overflow-hidden">
          {["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"].map(d => (
            <div key={d} className="bg-surface-elevated py-2 text-center text-xs font-semibold text-ink-muted">
              {d}
            </div>
          ))}
          {Array.from({ length: firstDayNormalized }).map((_, i) => (
            <div key={`empty-${i}`} className="bg-surface min-h-[100px]" />
          ))}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const dateNum = i + 1;
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(dateNum).padStart(2, '0')}`;
            const isToday = dateStr === todayISO();
            const dayApps = appsByDate[dateStr] || [];
            return (
              <div
                key={dateNum}
                onClick={() => {
                  setSelectedDate(dateStr);
                  setViewMode("LIST");
                }}
                className={`min-h-[100px] p-2 cursor-pointer transition-colors ${dayApps.length > 0 ? "bg-surface-elevated" : "bg-surface"} hover:bg-surface-elevated/80 border-t border-border group`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full ${isToday ? "bg-accent text-white" : "text-ink group-hover:text-accent"}`}>
                    {dateNum}
                  </span>
                </div>
                <div className="mt-1 flex flex-col gap-1">
                  {dayApps.slice(0, 3).map((a, idx) => (
                    <div key={idx} className="flex items-center gap-1 text-[10px] truncate rounded px-1 py-0.5" style={{ backgroundColor: `color-mix(in srgb, \${statusStyles[a.status].color} 15%, transparent)`, color: statusStyles[a.status].color }}>
                      <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: statusStyles[a.status].color }} />
                      <span className="truncate">{toHm(a.start_time)} {a.customer_name}</span>
                    </div>
                  ))}
                  {dayApps.length > 3 && (
                    <div className="text-[10px] text-ink-muted px-1">+{dayApps.length - 3} daha</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div
        className="flex flex-wrap items-center justify-between gap-4 border-l-2 pl-3"
        style={{ borderColor: "var(--agent-appointments)" }}
      >
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Randevu ajanı</h1>
          <p className="text-sm text-ink-muted">Günlük randevu takvimini görüntüle ve yönet.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-surface-elevated rounded-md border border-border p-1">
            <button
              onClick={() => setViewMode("LIST")}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                viewMode === "LIST" ? "bg-accent text-white" : "text-ink-muted hover:text-ink"
              }`}
            >
              <List className="h-3.5 w-3.5" /> Liste
            </button>
            <button
              onClick={() => setViewMode("CALENDAR")}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                viewMode === "CALENDAR" ? "bg-accent text-white" : "text-ink-muted hover:text-ink"
              }`}
            >
              <CalendarIcon className="h-3.5 w-3.5" /> Takvim
            </button>
          </div>
          <Button variant="outline" className="gap-2" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Dışa Aktar
          </Button>
          {viewMode === "LIST" && (
            <>
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-auto"
              />
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as AppointmentStatus | "ALL")}
                className="w-auto"
              >
                <option value="ALL">Tüm durumlar</option>
                {(Object.keys(statusStyles) as AppointmentStatus[]).map((s) => (
                  <option key={s} value={s}>
                    {statusStyles[s].label}
                  </option>
                ))}
              </Select>
            </>
          )}
          {!showCreateForm && (
            <Button className="gap-2" onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4" />
              Yeni randevu
            </Button>
          )}
        </div>
      </div>

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>}

      {viewMode === "CALENDAR" ? renderCalendar() : (
        <>
          {slots.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-ink-muted">Uygun saatler:</span>
          {slots.map((s) => (
            <button
              key={s}
              onClick={() => {
                setShowCreateForm(true);
                setCreateForm((f) => ({ ...f, start_time: toHm(s) }));
              }}
              className="rounded-full border border-border bg-surface-elevated px-3 py-1 text-xs font-medium text-ink hover:border-accent hover:text-accent"
            >
              {toHm(s)}
            </button>
          ))}
        </div>
      )}

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {selectedDate} için yeni randevu
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="a-customer">Müşteri</Label>
                <Select
                  id="a-customer"
                  value={createForm.customer_id}
                  onChange={(e) => applyCustomerSelection(e.target.value, setCreateForm)}
                >
                  <option value="">Listeden seç ya da aşağıya elle yaz</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                      {c.phone ? ` · ${c.phone}` : ""}
                    </option>
                  ))}
                </Select>
                {customers.length === 0 && (
                  <p className="text-xs text-ink-muted">
                    Henüz kayıtlı müşteri yok — &quot;Müşteriler&quot; sayfasından ekleyebilir ya da aşağıya
                    elle yazabilirsin.
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="a-name">Müşteri adı</Label>
                <Input
                  id="a-name"
                  value={createForm.customer_name}
                  onChange={(e) => setCreateForm((f) => ({ ...f, customer_name: e.target.value }))}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="a-phone">Telefon</Label>
                <Input
                  id="a-phone"
                  value={createForm.customer_phone}
                  onChange={(e) => setCreateForm((f) => ({ ...f, customer_phone: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="a-service">Hizmet</Label>
                <Select
                  id="a-service"
                  value={createForm.service_id}
                  onChange={(e) => applyServiceSelection(e.target.value, setCreateForm)}
                >
                  <option value="">Hizmet seçme (opsiyonel)</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} · ₺{s.price}
                      {s.duration_minutes ? ` · ${s.duration_minutes} dk` : ""}
                    </option>
                  ))}
                </Select>
                {services.length === 0 && (
                  <p className="text-xs text-ink-muted">
                    Henüz kayıtlı hizmet yok — &quot;Satış ve öneri ajanı&quot; sayfasından ekleyebilirsin.
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="a-start">Başlangıç saati</Label>
                <Input
                  id="a-start"
                  type="time"
                  value={createForm.start_time}
                  onChange={(e) => setCreateForm((f) => ({ ...f, start_time: e.target.value }))}
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="a-end">Bitiş saati</Label>
                <Input
                  id="a-end"
                  type="time"
                  value={createForm.end_time}
                  onChange={(e) => setCreateForm((f) => ({ ...f, end_time: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="a-notes">Notlar</Label>
                <Input
                  id="a-notes"
                  value={createForm.notes}
                  onChange={(e) => setCreateForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </div>
              <div className="flex gap-2 sm:col-span-2">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowCreateForm(false);
                    setCreateForm(emptyForm);
                  }}
                >
                  Vazgeç
                </Button>
                <Button type="submit" disabled={creating} className="flex-1">
                  {creating ? "Oluşturuluyor..." : "Randevu oluştur"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : filteredAppointments.length === 0 ? (
        <p className="text-sm text-ink-muted">{selectedDate} için randevu yok.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {filteredAppointments
            .slice()
            .sort((a, b) => a.start_time.localeCompare(b.start_time))
            .map((a) => {
              const style = statusStyles[a.status];
              return (
                <Card key={a.id} className="border-l-2" style={{ borderLeftColor: style.color }}>
                  <CardContent className="p-4">
                    {editingId === a.id ? (
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <Select
                          value={editForm.customer_id}
                          onChange={(e) => applyCustomerSelection(e.target.value, setEditForm)}
                          className="sm:col-span-2"
                        >
                          <option value="">Listeden seç ya da elle yaz</option>
                          {customers.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                              {c.phone ? ` · ${c.phone}` : ""}
                            </option>
                          ))}
                        </Select>
                        <Input
                          value={editForm.customer_name}
                          onChange={(e) => setEditForm((f) => ({ ...f, customer_name: e.target.value }))}
                          placeholder="Müşteri adı"
                        />
                        <Input
                          value={editForm.customer_phone}
                          onChange={(e) => setEditForm((f) => ({ ...f, customer_phone: e.target.value }))}
                          placeholder="Telefon"
                        />
                        <Select
                          value={editForm.service_id}
                          onChange={(e) => applyServiceSelection(e.target.value, setEditForm)}
                          className="sm:col-span-2"
                        >
                          <option value="">Hizmet seçme (opsiyonel)</option>
                          {services.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} · ₺{s.price}
                              {s.duration_minutes ? ` · ${s.duration_minutes} dk` : ""}
                            </option>
                          ))}
                        </Select>
                        <Input
                          type="time"
                          value={editForm.start_time}
                          onChange={(e) => setEditForm((f) => ({ ...f, start_time: e.target.value }))}
                        />
                        <Input
                          type="time"
                          value={editForm.end_time}
                          onChange={(e) => setEditForm((f) => ({ ...f, end_time: e.target.value }))}
                        />
                        <Input
                          value={editForm.notes}
                          onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
                          placeholder="Notlar"
                          className="sm:col-span-2"
                        />
                        <div className="flex gap-2 sm:col-span-2">
                          <Button variant="outline" className="flex-1" onClick={() => setEditingId(null)}>
                            Vazgeç
                          </Button>
                          <Button
                            className="flex-1"
                            disabled={savingEdit}
                            onClick={() => handleSaveEdit(a.id)}
                          >
                            {savingEdit ? "Kaydediliyor..." : "Kaydet"}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="flex items-center gap-1 font-medium text-ink">
                              <Clock className="h-3.5 w-3.5" style={{ color: style.color }} />
                              {toHm(a.start_time)}
                              {a.end_time && ` - ${toHm(a.end_time)}`}
                            </span>
                            <span
                              className="rounded-full px-2 py-0.5 text-xs font-medium"
                              style={{
                                backgroundColor: `color-mix(in srgb, ${style.color} 15%, transparent)`,
                                color: style.color,
                              }}
                            >
                              {style.label}
                            </span>
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-ink-muted">
                            <span className="flex items-center gap-1">
                              <UserIcon className="h-3.5 w-3.5" />
                              {a.customer_name}
                            </span>
                            {a.customer_phone && (
                              <span className="flex items-center gap-1">
                                <Phone className="h-3.5 w-3.5" />
                                {a.customer_phone}
                              </span>
                            )}
                          </div>
                          {a.notes && <p className="mt-1 text-sm text-ink-muted">{a.notes}</p>}
                        </div>
                        <div className="flex shrink-0 gap-1">
                          {(a.status === "PENDING" || a.status === "CONFIRMED") && (
                            <>
                              <Button variant="ghost" size="icon" onClick={() => startEdit(a)}>
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={() => handleComplete(a.id)}>
                                <Check className="h-4 w-4" style={{ color: "var(--agent-sales)" }} />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={() => handleCancel(a.id)}>
                                <X className="h-4 w-4 text-danger" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
        </div>
      )}
        </>
      )}
    </div>
  );
}
