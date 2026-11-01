"use client";

import { useState, type Dispatch, type SetStateAction } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type {
  Appointment,
  AppointmentCreatePayload,
  Branch,
  BusinessService,
  Customer,
  StaffProfile,
} from "@/lib/api";
import { addMinutes, toHm, toHms } from "@/lib/date";
import { cn } from "@/lib/utils";

export interface AppointmentFormValues {
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  service_id: string;
  staff_id: string;
  branch_id: string;
  appointment_date: string;
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  notes: string;
}

export function emptyFormValues(date: string, startTime = "", branchId: string | null = null): AppointmentFormValues {
  return {
    customer_id: "",
    customer_name: "",
    customer_phone: "",
    customer_email: "",
    service_id: "",
    staff_id: "",
    branch_id: branchId ?? "",
    appointment_date: date,
    start_time: startTime,
    end_time: "",
    notes: "",
  };
}

export function formValuesFrom(a: Appointment): AppointmentFormValues {
  return {
    customer_id: a.customer_id ?? "",
    customer_name: a.customer_name,
    customer_phone: a.customer_phone ?? "",
    customer_email: a.customer_email ?? "",
    service_id: a.service_id ?? "",
    staff_id: a.staff_id ?? "",
    branch_id: a.branch_id ?? "",
    appointment_date: a.appointment_date,
    start_time: toHm(a.start_time),
    end_time: a.end_time ? toHm(a.end_time) : "",
    notes: a.notes ?? "",
  };
}

/** Oluşturma ve güncelleme için aynı gövde (güncellemede tüm alanlar gönderilir). */
export function toPayload(v: AppointmentFormValues): AppointmentCreatePayload {
  return {
    customer_name: v.customer_name,
    customer_phone: v.customer_phone || null,
    customer_email: v.customer_email || null,
    customer_id: v.customer_id || null,
    service_id: v.service_id || null,
    staff_id: v.staff_id || null,
    branch_id: v.branch_id || null,
    appointment_date: v.appointment_date,
    start_time: toHms(v.start_time),
    end_time: v.end_time ? toHms(v.end_time) : null,
    notes: v.notes || null,
  };
}

interface Props {
  idPrefix: string;
  values: AppointmentFormValues;
  onChange: Dispatch<SetStateAction<AppointmentFormValues>>;
  customers: Customer[];
  services: BusinessService[];
  staff: StaffProfile[];
  branches: Branch[];
  /** Liste görünümünde tarih yukarıdaki seçiciden gelir; takvimde formda seçilir. */
  showDate?: boolean;
  submitLabel: string;
  submittingLabel: string;
  onSubmit: (values: AppointmentFormValues) => Promise<void>;
  onCancel: () => void;
  className?: string;
}

export function AppointmentForm({
  idPrefix,
  values: v,
  onChange: setV,
  customers,
  services,
  staff,
  branches,
  showDate = true,
  submitLabel,
  submittingLabel,
  onSubmit,
  onCancel,
  className,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const id = (name: string) => `${idPrefix}-${name}`;
  const set = (patch: Partial<AppointmentFormValues>) => setV((prev) => ({ ...prev, ...patch }));

  function selectCustomer(customerId: string) {
    const c = customers.find((x) => x.id === customerId);
    setV((f) => ({
      ...f,
      customer_id: customerId,
      customer_name: c ? c.name : f.customer_name,
      customer_phone: c?.phone ?? f.customer_phone,
      customer_email: c?.email ?? f.customer_email,
    }));
  }

  function selectService(serviceId: string) {
    const s = services.find((x) => x.id === serviceId);
    setV((f) => ({
      ...f,
      service_id: serviceId,
      end_time: s?.duration_minutes && f.start_time ? addMinutes(f.start_time, s.duration_minutes) : f.end_time,
    }));
  }

  function selectStaff(staffId: string) {
    const s = staff.find((x) => x.id === staffId);
    // Personelin şubesi varsa randevu o şubeye yazılır; takvimin şube filtresi tutarlı kalsın.
    setV((f) => ({ ...f, staff_id: staffId, branch_id: s?.branch_id ?? f.branch_id }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(v);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cn("grid grid-cols-1 gap-4 sm:grid-cols-2", className)}>
      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <Label htmlFor={id("customer")}>Müşteri</Label>
        <Select id={id("customer")} value={v.customer_id} onChange={(e) => selectCustomer(e.target.value)}>
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
            Henüz kayıtlı müşteri yok — &quot;Müşteriler&quot; sayfasından ekleyebilir ya da aşağıya elle yazabilirsin.
          </p>
        )}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={id("name")}>Müşteri adı</Label>
        <Input id={id("name")} value={v.customer_name} onChange={(e) => set({ customer_name: e.target.value })} required />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={id("phone")}>Telefon</Label>
        <Input id={id("phone")} value={v.customer_phone} onChange={(e) => set({ customer_phone: e.target.value })} />
      </div>
      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <Label htmlFor={id("service")}>Hizmet</Label>
        <Select id={id("service")} value={v.service_id} onChange={(e) => selectService(e.target.value)}>
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
      {staff.length > 0 && (
        <div className={cn("flex flex-col gap-1.5", branches.length <= 1 && "sm:col-span-2")}>
          <Label htmlFor={id("staff")}>Personel</Label>
          <Select id={id("staff")} value={v.staff_id} onChange={(e) => selectStaff(e.target.value)}>
            <option value="">Personel seçme (opsiyonel)</option>
            {staff.map((s) => (
              <option key={s.id} value={s.id}>
                {s.full_name}
              </option>
            ))}
          </Select>
        </div>
      )}
      {branches.length > 1 && (
        <div className={cn("flex flex-col gap-1.5", staff.length === 0 && "sm:col-span-2")}>
          <Label htmlFor={id("branch")}>Şube</Label>
          <Select id={id("branch")} value={v.branch_id} onChange={(e) => set({ branch_id: e.target.value })}>
            <option value="">Şube seçme (opsiyonel)</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
        </div>
      )}
      {showDate && (
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor={id("date")}>Tarih</Label>
          <Input
            id={id("date")}
            type="date"
            value={v.appointment_date}
            onChange={(e) => set({ appointment_date: e.target.value })}
            required
          />
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={id("start")}>Başlangıç saati</Label>
        <Input
          id={id("start")}
          type="time"
          value={v.start_time}
          onChange={(e) => set({ start_time: e.target.value })}
          required
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={id("end")}>Bitiş saati</Label>
        <Input id={id("end")} type="time" value={v.end_time} onChange={(e) => set({ end_time: e.target.value })} />
      </div>
      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <Label htmlFor={id("notes")}>Notlar</Label>
        <Input id={id("notes")} value={v.notes} onChange={(e) => set({ notes: e.target.value })} />
      </div>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="button" variant="outline" className="flex-1" onClick={onCancel}>
          Vazgeç
        </Button>
        <Button type="submit" disabled={submitting} className="flex-1">
          {submitting ? submittingLabel : submitLabel}
        </Button>
      </div>
    </form>
  );
}
