"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Clock, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listScheduleBlocks,
  createScheduleBlock,
  updateScheduleBlock,
  deleteScheduleBlock,
  ApiError,
  BlockType,
  RecurrenceDay,
  ScheduleBlock
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

const emptyForm = {
  block_type: "TIME_RANGE" as BlockType,
  title: "",
  start_date: "",
  end_date: "",
  start_time: "",
  end_time: "",
  recurrence_day: "" as RecurrenceDay | "",
  reason: "",
};

const typeLabels: Record<BlockType, string> = {
  FULL_DAY: "Tüm Gün",
  TIME_RANGE: "Saat Aralığı",
  RECURRING: "Tekrarlayan",
};

const dayLabels: Record<RecurrenceDay, string> = {
  MONDAY: "Pazartesi",
  TUESDAY: "Salı",
  WEDNESDAY: "Çarşamba",
  THURSDAY: "Perşembe",
  FRIDAY: "Cuma",
  SATURDAY: "Cumartesi",
  SUNDAY: "Pazar",
};

export default function ScheduleSettingsPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();
  const [loading, setLoading] = useState(true);
  const [blocks, setBlocks] = useState<ScheduleBlock[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadData = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      const data = await listScheduleBlocks(businessId);
      setBlocks(data);
    } catch (err) {
      toast.error("Bloklar yüklenirken bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [businessId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!businessId) return;
    setSaving(true);
    try {
      const payload: any = {
        block_type: form.block_type,
        title: form.title || null,
        reason: form.reason || null,
        is_active: true,
      };

      if (form.block_type === "FULL_DAY") {
        payload.start_date = form.start_date;
        payload.end_date = form.end_date || null;
      } else if (form.block_type === "TIME_RANGE") {
        payload.start_date = form.start_date;
        payload.start_time = form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time;
        payload.end_time = form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time;
      } else if (form.block_type === "RECURRING") {
        payload.recurrence_day = form.recurrence_day;
        payload.start_time = form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time;
        payload.end_time = form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time;
      }

      if (editingId) {
        await updateScheduleBlock(businessId, editingId, payload);
        toast.success("Blok güncellendi.");
      } else {
        await createScheduleBlock(businessId, payload);
        toast.success("Yeni blok eklendi.");
      }
      setShowForm(false);
      setForm(emptyForm);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Kaydedilirken hata oluştu.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Blok Sil",
      description: "Bu çalışma bloğunu silmek istediğinize emin misiniz?",
    });
    if (!ok) return;

    try {
      await deleteScheduleBlock(businessId, id);
      toast.success("Blok silindi.");
      loadData();
    } catch (err) {
      toast.error("Silinirken hata oluştu.");
    }
  };

  const startEdit = (block: ScheduleBlock) => {
    setForm({
      block_type: block.block_type,
      title: block.title || "",
      start_date: block.start_date || "",
      end_date: block.end_date || "",
      start_time: block.start_time?.slice(0, 5) || "",
      end_time: block.end_time?.slice(0, 5) || "",
      recurrence_day: block.recurrence_day || "",
      reason: block.reason || "",
    });
    setEditingId(block.id);
    setShowForm(true);
  };

  return (
    <div className="flex flex-col gap-6">
      <div
        className="flex flex-wrap items-center justify-between gap-4 border-l-2 pl-3"
        style={{ borderColor: "var(--agent-appointments)" }}
      >
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Çalışma Saatleri ve Bloklar</h1>
          <p className="text-sm text-ink-muted">Randevu alınamayacak saat ve günleri yönetin.</p>
        </div>
        {!showForm && (
          <Button className="gap-2" onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4" />
            Yeni blok ekle
          </Button>
        )}
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{editingId ? "Bloğu Düzenle" : "Yeni Blok Ekle"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label>Blok Tipi</Label>
                <Select
                  value={form.block_type}
                  onChange={(e) => setForm({ ...form, block_type: e.target.value as BlockType })}
                >
                  <option value="FULL_DAY">Tüm Gün</option>
                  <option value="TIME_RANGE">Saat Aralığı</option>
                  <option value="RECURRING">Tekrarlayan (Haftalık)</option>
                </Select>
              </div>

              {form.block_type === "FULL_DAY" && (
                <>
                  <div className="flex flex-col gap-1.5">
                    <Label>Başlangıç Tarihi</Label>
                    <Input
                      type="date"
                      value={form.start_date}
                      onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Bitiş Tarihi (Opsiyonel)</Label>
                    <Input
                      type="date"
                      value={form.end_date}
                      onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                    />
                  </div>
                </>
              )}

              {form.block_type === "TIME_RANGE" && (
                <>
                  <div className="flex flex-col gap-1.5 sm:col-span-2">
                    <Label>Tarih</Label>
                    <Input
                      type="date"
                      value={form.start_date}
                      onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Başlangıç Saati</Label>
                    <Input
                      type="time"
                      value={form.start_time}
                      onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Bitiş Saati</Label>
                    <Input
                      type="time"
                      value={form.end_time}
                      onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                      required
                    />
                  </div>
                </>
              )}

              {form.block_type === "RECURRING" && (
                <>
                  <div className="flex flex-col gap-1.5 sm:col-span-2">
                    <Label>Gün</Label>
                    <Select
                      value={form.recurrence_day}
                      onChange={(e) => setForm({ ...form, recurrence_day: e.target.value as RecurrenceDay })}
                      required
                    >
                      <option value="">Seçiniz...</option>
                      {Object.entries(dayLabels).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Başlangıç Saati</Label>
                    <Input
                      type="time"
                      value={form.start_time}
                      onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label>Bitiş Saati</Label>
                    <Input
                      type="time"
                      value={form.end_time}
                      onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                      required
                    />
                  </div>
                </>
              )}

              <div className="flex flex-col gap-1.5">
                <Label>Başlık (Opsiyonel)</Label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Örn: Öğle arası"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label>Sebep (Opsiyonel)</Label>
                <Input
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  placeholder="Örn: Tadilat"
                />
              </div>

              <div className="flex gap-2 sm:col-span-2 mt-2">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowForm(false);
                    setForm(emptyForm);
                    setEditingId(null);
                  }}
                >
                  İptal
                </Button>
                <Button type="submit" disabled={saving} className="flex-1">
                  {saving ? "Kaydediliyor..." : "Kaydet"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : blocks.length === 0 ? (
        <p className="text-sm text-ink-muted">Kayıtlı blok bulunmamaktadır.</p>
      ) : (
        <div className="grid gap-3">
          {blocks.map((block) => (
            <Card key={block.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: "color-mix(in srgb, var(--agent-appointments) 15%, transparent)",
                        color: "var(--agent-appointments)",
                      }}
                    >
                      {typeLabels[block.block_type]}
                    </span>
                    <span className="font-medium text-ink">{block.title || "İsimsiz Blok"}</span>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-ink-muted mt-1">
                    {block.block_type === "FULL_DAY" && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        {block.start_date} {block.end_date && ` - ${block.end_date}`}
                      </span>
                    )}
                    {block.block_type === "TIME_RANGE" && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {block.start_date} ({block.start_time?.slice(0, 5)} - {block.end_time?.slice(0, 5)})
                      </span>
                    )}
                    {block.block_type === "RECURRING" && block.recurrence_day && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        Her {dayLabels[block.recurrence_day]} ({block.start_time?.slice(0, 5)} - {block.end_time?.slice(0, 5)})
                      </span>
                    )}
                  </div>
                  {block.reason && <p className="text-xs text-ink-muted mt-1">Sebep: {block.reason}</p>}
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" onClick={() => startEdit(block)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => handleDelete(block.id)}>
                    <Trash2 className="h-4 w-4 text-danger" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
