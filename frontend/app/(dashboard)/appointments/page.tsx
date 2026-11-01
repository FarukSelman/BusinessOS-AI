"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { Plus, Clock, User as UserIcon, Phone, Check, X, Pencil, List, Calendar as CalendarIcon, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  listServices,
  listStaff,
  listBranches,
  type Appointment,
  type AppointmentStatus,
  type Branch,
  type BusinessService,
  type StaffProfile,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { todayISO, toHm } from "@/lib/date";
import { useDeepLink } from "@/lib/use-deep-link";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import { useCsvExport } from "@/lib/use-csv-export";
import { statusStyles } from "@/components/appointments/constants";
import {
  AppointmentForm,
  emptyFormValues,
  formValuesFrom,
  toPayload,
  type AppointmentFormValues,
} from "@/components/appointments/appointment-form";
import {
  AppointmentDetailDialog,
  AppointmentFormDialog,
  type FormDialogState,
} from "@/components/appointments/appointment-dialogs";
import { AppointmentCalendar } from "@/components/appointments/calendar/appointment-calendar";

// useSearchParams (global aramadan gelen ?date=&open=) bir Suspense sınırı ister.
export default function AppointmentsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink-muted">Yükleniyor...</p>}>
      <AppointmentsPageContent />
    </Suspense>
  );
}

function AppointmentsPageContent() {
  const confirmDialog = useConfirm();
  const csvExport = useCsvExport();
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "ALL">("ALL");
  const businessId = getActiveBusinessId();

  const [viewMode, setViewMode] = useState<"LIST" | "CALENDAR">("LIST");
  // Liste ve takvim aynı günü paylaşır: takvimde gezilen gün listeye geçince de seçili kalır.
  const [selectedDate, setSelectedDate] = useState(todayISO());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [services, setServices] = useState<BusinessService[]>([]);
  const [staff, setStaff] = useState<StaffProfile[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<AppointmentFormValues>(() => emptyFormValues(todayISO()));

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AppointmentFormValues>(() => emptyFormValues(todayISO()));

  // Takvim: bir randevu değişince artırılır, takvim yeniden çekilir.
  const [calendarRefreshKey, setCalendarRefreshKey] = useState(0);
  const [detailId, setDetailId] = useState<string | null>(null);
  // Global aramadan gelen randevu: o güne git, detayını aç.
  useDeepLink(["date", "open"], ({ date, open }) => {
    if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) setSelectedDate(date);
    if (open) setDetailId(open);
  });
  const [formDialog, setFormDialog] = useState<FormDialogState | null>(null);

  // Dropdown listeleri - bir kez, tarih değişse de yeniden çekilmesine gerek yok
  useEffect(() => {
    if (!businessId) return;
    listServices(businessId).then(setServices).catch(() => setServices([]));
    listStaff(businessId)
      .then((s) => setStaff(s as StaffProfile[]))
      .catch(() => setStaff([]));
    listBranches(businessId)
      .then((b) => setBranches((b as Branch[]).filter((x) => x.is_active)))
      .catch(() => setBranches([]));
  }, [businessId]);

  function handleExport() {
    if (!businessId) return;
    const serviceName = new Map(services.map((s) => [s.id, s.name]));
    csvExport.run(
      "Randevular",
      ["Müşteri", "Hizmet", "Tarih", "Saat", "Durum", "Notlar"],
      (page, size) => listAppointments(businessId, page, size),
      (a) => [
        a.customer_name,
        (a.service_id && serviceName.get(a.service_id)) || "",
        a.appointment_date,
        a.start_time,
        statusStyles[a.status].label,
        a.notes || "",
      ]
    );
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

  // Günlük liste sadece liste görünümünde çekilir; takvim kendi aralığını çeker.
  useEffect(() => {
    if (viewMode === "LIST") loadData();
  }, [loadData, viewMode]);

  const refreshAll = useCallback(() => {
    setCalendarRefreshKey((k) => k + 1);
    if (viewMode === "LIST") loadData();
  }, [loadData, viewMode]);

  const filteredAppointments = appointments.filter((a) =>
    statusFilter === "ALL" ? true : a.status === statusFilter
  );

  async function handleCreate(values: AppointmentFormValues) {
    if (!businessId) return;
    setError(null);
    try {
      await createAppointment(businessId, toPayload({ ...values, appointment_date: selectedDate }));
      setCreateForm(emptyFormValues(selectedDate));
      setShowCreateForm(false);
      toast.success("Randevu oluşturuldu.");
      refreshAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Randevu oluşturulamadı.");
    }
  }

  function startEdit(a: Appointment) {
    setEditingId(a.id);
    setEditForm(formValuesFrom(a));
  }

  async function handleSaveEdit(appointmentId: string, values: AppointmentFormValues) {
    if (!businessId) return;
    setError(null);
    try {
      await updateAppointment(businessId, appointmentId, toPayload(values));
      setEditingId(null);
      toast.success("Güncellendi.");
      refreshAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Güncellenemedi.");
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
      refreshAll();
      toast.success("Randevu iptal edildi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İptal edilemedi.");
    }
  }

  async function handleComplete(appointmentId: string) {
    if (!businessId) return;
    try {
      await completeAppointment(businessId, appointmentId);
      refreshAll();
      toast.success("Randevu tamamlandı.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Tamamlanamadı.");
    }
  }

  async function handleDialogSubmit(state: FormDialogState, values: AppointmentFormValues) {
    if (!businessId) return;
    try {
      if (state.mode === "create") {
        await createAppointment(businessId, toPayload(values));
        toast.success("Randevu oluşturuldu.");
      } else {
        await updateAppointment(businessId, state.appointmentId, toPayload(values));
        toast.success("Güncellendi.");
      }
      setFormDialog(null);
      refreshAll();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Kaydedilemedi.");
    }
  }

  const openCreateDialog = useCallback((date: string, time = "") => {
    setFormDialog({ mode: "create", initial: emptyFormValues(date, time) });
  }, []);

  const staffById = new Map(staff.map((s) => [s.id, s]));
  // Eski randevular pasif personelin rengini/adını göstermeye devam eder; yeni atama sadece aktiflere.
  const activeStaff = staff.filter((s) => s.status !== "INACTIVE");

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
        <div className="flex flex-wrap items-center gap-3">
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
          <Button variant="outline" className="gap-2" onClick={handleExport} disabled={csvExport.exporting}>
            <Download className="h-4 w-4" />
            {csvExport.exporting ? "Hazırlanıyor..." : "Dışa Aktar"}
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
          {viewMode === "CALENDAR" ? (
            <Button className="gap-2" onClick={() => openCreateDialog(selectedDate)}>
              <Plus className="h-4 w-4" />
              Yeni randevu
            </Button>
          ) : (
            !showCreateForm && (
              <Button className="gap-2" onClick={() => setShowCreateForm(true)}>
                <Plus className="h-4 w-4" />
                Yeni randevu
              </Button>
            )
          )}
        </div>
      </div>

      {error && <p className="rounded-md bg-danger-soft p-3 text-sm text-danger">{error}</p>}

      {viewMode === "CALENDAR" && businessId ? (
        <AppointmentCalendar
          businessId={businessId}
          date={selectedDate}
          onDateChange={setSelectedDate}
          services={services}
          staff={staff}
          branches={branches}
          refreshKey={calendarRefreshKey}
          onSelectAppointment={setDetailId}
          onSlotClick={openCreateDialog}
        />
      ) : (
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
                  className="rounded-full border border-border bg-surface-elevated px-3 py-1 text-xs font-medium text-ink hover:border-accent hover:text-accent-text"
                >
                  {toHm(s)}
                </button>
              ))}
            </div>
          )}

          {showCreateForm && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{selectedDate} için yeni randevu</CardTitle>
              </CardHeader>
              <CardContent>
                <AppointmentForm
                  idPrefix="a"
                  values={createForm}
                  onChange={setCreateForm}
                  services={services}
                  staff={activeStaff}
                  branches={branches}
                  showDate={false}
                  submitLabel="Randevu oluştur"
                  submittingLabel="Oluşturuluyor..."
                  onSubmit={handleCreate}
                  onCancel={() => {
                    setShowCreateForm(false);
                    setCreateForm(emptyFormValues(selectedDate));
                  }}
                />
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
                  const member = a.staff_id ? staffById.get(a.staff_id) : undefined;
                  return (
                    <Card key={a.id} className="border-l-2" style={{ borderLeftColor: style.color }}>
                      <CardContent className="p-4">
                        {editingId === a.id ? (
                          <AppointmentForm
                            idPrefix={`e-${a.id}`}
                            values={editForm}
                            onChange={setEditForm}
                            services={services}
                            staff={activeStaff}
                            branches={branches}
                            submitLabel="Kaydet"
                            submittingLabel="Kaydediliyor..."
                            onSubmit={(values) => handleSaveEdit(a.id, values)}
                            onCancel={() => setEditingId(null)}
                          />
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
                                  style={{ backgroundColor: style.soft, color: style.color }}
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
                                {member && (
                                  <span className="flex items-center gap-1.5">
                                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: member.color }} />
                                    {member.full_name}
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

      {businessId && (
        <AppointmentDetailDialog
          businessId={businessId}
          appointmentId={detailId}
          services={services}
          staff={staff}
          branches={branches}
          onClose={() => setDetailId(null)}
          onEdit={(a) => {
            setDetailId(null);
            setFormDialog({ mode: "edit", appointmentId: a.id, initial: formValuesFrom(a) });
          }}
          onChanged={refreshAll}
        />
      )}
      <AppointmentFormDialog
        state={formDialog}
        services={services}
        staff={activeStaff}
        branches={branches}
        onClose={() => setFormDialog(null)}
        onSubmit={handleDialogSubmit}
      />
    </div>
  );
}
