"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { Check, Clock, Mail, MapPin, Pencil, Phone, Scissors, User as UserIcon, UserX, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";
import {
  ApiError,
  cancelAppointment,
  completeAppointment,
  getAppointment,
  updateAppointment,
  type Appointment,
  type Branch,
  type BusinessService,
  type StaffProfile,
} from "@/lib/api";
import { fromISODate, toHm } from "@/lib/date";
import { AppointmentForm, type AppointmentFormValues } from "./appointment-form";
import { statusStyles } from "./constants";

interface Lookups {
  services: BusinessService[];
  staff: StaffProfile[];
  branches: Branch[];
}

function hasStarted(a: Appointment) {
  const [h, m] = a.start_time.split(":").map(Number);
  const start = fromISODate(a.appointment_date);
  start.setHours(h, m);
  return start.getTime() <= Date.now();
}

// --------------------------------------------------
// Detay
// --------------------------------------------------

interface DetailProps extends Lookups {
  businessId: string;
  appointmentId: string | null;
  onClose: () => void;
  onEdit: (appointment: Appointment) => void;
  onChanged: () => void;
}

export function AppointmentDetailDialog({
  businessId,
  appointmentId,
  services,
  staff,
  branches,
  onClose,
  onEdit,
  onChanged,
}: DetailProps) {
  const confirmDialog = useConfirm();
  const [loaded, setLoaded] = useState<{ id: string; appointment: Appointment | null; error: string | null } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!appointmentId) return;
    let active = true;
    getAppointment(businessId, appointmentId)
      .then((a) => active && setLoaded({ id: appointmentId, appointment: a, error: null }))
      .catch(
        (err) =>
          active &&
          setLoaded({
            id: appointmentId,
            appointment: null,
            error: err instanceof ApiError ? err.message : "Randevu yüklenemedi.",
          })
      );
    return () => {
      active = false;
    };
  }, [businessId, appointmentId]);

  const current = loaded?.id === appointmentId ? loaded : null;
  const a = current?.appointment ?? null;

  async function run(action: () => Promise<Appointment>, success: string) {
    setBusy(true);
    try {
      const updated = await action();
      setLoaded({ id: updated.id, appointment: updated, error: null });
      toast.success(success);
      onChanged();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem yapılamadı.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCancel(appt: Appointment) {
    const ok = await confirmDialog({
      title: "Randevuyu iptal et",
      description: "Bu randevuyu iptal etmek istediğine emin misin?",
    });
    if (ok) run(() => cancelAppointment(businessId, appt.id), "Randevu iptal edildi.");
  }

  const status = a ? statusStyles[a.status] : null;
  const service = a?.service_id ? services.find((s) => s.id === a.service_id) : undefined;
  const member = a?.staff_id ? staff.find((s) => s.id === a.staff_id) : undefined;
  const branch = a?.branch_id ? branches.find((b) => b.id === a.branch_id) : undefined;
  const active = a && (a.status === "PENDING" || a.status === "CONFIRMED");

  return (
    <Dialog open={appointmentId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="w-[calc(100%-2rem)] max-w-md">
        {!current ? (
          <>
            <DialogTitle>Randevu</DialogTitle>
            <DialogDescription>Yükleniyor...</DialogDescription>
          </>
        ) : !a || !status ? (
          <>
            <DialogTitle>Randevu</DialogTitle>
            <DialogDescription className="text-danger">{current.error}</DialogDescription>
          </>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-start justify-between gap-3 pr-2">
              <div className="min-w-0">
                <DialogTitle className="truncate">{a.customer_name}</DialogTitle>
                <DialogDescription className="mt-1 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  {format(fromISODate(a.appointment_date), "d MMMM yyyy, EEEE", { locale: tr })} ·{" "}
                  {toHm(a.start_time)}
                  {a.end_time && `–${toHm(a.end_time)}`}
                </DialogDescription>
              </div>
              <span
                className="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ backgroundColor: status.soft, color: status.color }}
              >
                {status.label}
              </span>
            </div>

            <dl className="grid gap-2 text-sm">
              {service && (
                <Row icon={<Scissors className="h-3.5 w-3.5" />}>
                  {service.name}
                  {service.duration_minutes ? ` · ${service.duration_minutes} dk` : ""} · ₺{service.price}
                </Row>
              )}
              {member && (
                <Row icon={<span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: member.color }} />}>
                  {member.full_name}
                </Row>
              )}
              {branch && <Row icon={<MapPin className="h-3.5 w-3.5" />}>{branch.name}</Row>}
              {a.customer_phone && (
                <Row icon={<Phone className="h-3.5 w-3.5" />}>
                  <a href={`tel:${a.customer_phone}`} className="hover:text-accent-text">
                    {a.customer_phone}
                  </a>
                </Row>
              )}
              {a.customer_email && <Row icon={<Mail className="h-3.5 w-3.5" />}>{a.customer_email}</Row>}
              {!service && !member && !a.customer_phone && (
                <Row icon={<UserIcon className="h-3.5 w-3.5" />}>Ek bilgi yok</Row>
              )}
            </dl>
            {a.notes && <p className="rounded-md bg-surface p-3 text-sm text-ink-muted">{a.notes}</p>}

            {active && (
              <div className="flex flex-wrap gap-2 border-t border-border pt-4">
                {a.status === "PENDING" && (
                  <Button
                    size="sm"
                    className="gap-1.5"
                    disabled={busy}
                    onClick={() => run(() => updateAppointment(businessId, a.id, { status: "CONFIRMED" }), "Randevu onaylandı.")}
                  >
                    <Check className="h-4 w-4" /> Onayla
                  </Button>
                )}
                <Button size="sm" className="gap-1.5" variant="outline" disabled={busy} onClick={() => onEdit(a)}>
                  <Pencil className="h-4 w-4" /> Düzenle
                </Button>
                <Button
                  size="sm"
                  className="gap-1.5"
                  variant="outline"
                  disabled={busy}
                  onClick={() => run(() => completeAppointment(businessId, a.id), "Randevu tamamlandı.")}
                >
                  <Check className="h-4 w-4" style={{ color: "var(--agent-sales)" }} /> Tamamla
                </Button>
                {hasStarted(a) && (
                  <Button
                    size="sm"
                    className="gap-1.5"
                    variant="outline"
                    disabled={busy}
                    onClick={() => run(() => updateAppointment(businessId, a.id, { status: "NO_SHOW" }), "Gelmedi olarak işaretlendi.")}
                  >
                    <UserX className="h-4 w-4" /> Gelmedi
                  </Button>
                )}
                <Button size="sm" className="gap-1.5" variant="outline" disabled={busy} onClick={() => handleCancel(a)}>
                  <X className="h-4 w-4 text-danger" /> İptal et
                </Button>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Row({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-ink">
      <span className="flex w-4 justify-center text-ink-muted">{icon}</span>
      <span className="min-w-0 truncate">{children}</span>
    </div>
  );
}

// --------------------------------------------------
// Oluştur / düzenle
// --------------------------------------------------

export type FormDialogState =
  | { mode: "create"; initial: AppointmentFormValues }
  | { mode: "edit"; appointmentId: string; initial: AppointmentFormValues };

interface FormDialogProps extends Lookups {
  state: FormDialogState | null;
  onClose: () => void;
  onSubmit: (state: FormDialogState, values: AppointmentFormValues) => Promise<void>;
}

export function AppointmentFormDialog({ state, services, staff, branches, onClose, onSubmit }: FormDialogProps) {
  return (
    <Dialog open={state !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] w-[calc(100%-2rem)] max-w-lg overflow-y-auto">
        {state && (
          <>
            <DialogTitle className="mb-4">{state.mode === "create" ? "Yeni randevu" : "Randevuyu düzenle"}</DialogTitle>
            <FormDialogBody
              // her açılışta form temiz başlasın
              key={state.mode === "edit" ? state.appointmentId : `${state.initial.appointment_date}-${state.initial.start_time}`}
              state={state}
              services={services}
              staff={staff}
              branches={branches}
              onClose={onClose}
              onSubmit={onSubmit}
            />
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function FormDialogBody({
  state,
  services,
  staff,
  branches,
  onClose,
  onSubmit,
}: Omit<FormDialogProps, "state"> & { state: FormDialogState }) {
  const [values, setValues] = useState(state.initial);
  return (
    <AppointmentForm
      idPrefix="dlg"
      values={values}
      onChange={setValues}
      services={services}
      staff={staff}
      branches={branches}
      submitLabel={state.mode === "create" ? "Randevu oluştur" : "Kaydet"}
      submittingLabel={state.mode === "create" ? "Oluşturuluyor..." : "Kaydediliyor..."}
      onSubmit={(v) => onSubmit(state, v)}
      onCancel={onClose}
    />
  );
}
