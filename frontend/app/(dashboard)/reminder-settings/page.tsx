"use client";

import React, { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Bell, Mail, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listReminderConfigs,
  createReminderConfig,
  updateReminderConfig,
  deleteReminderConfig,
  ApiError,
  ReminderConfig,
  ReminderChannelType
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

const emptyForm = {
  channel: "EMAIL" as ReminderChannelType,
  hours_before: 24,
  message_template: "Sayın {{customer_name}}, {{appointment_date}} saat {{start_time}}'da {{service_name}} randevunuz bulunmaktadır.",
  is_active: true,
};

const VARIABLE_LABELS: Record<string, string> = {
  customer_name: "Müşteri Adı",
  appointment_date: "Randevu Tarihi",
  start_time: "Başlangıç Saati",
  service_name: "Hizmet Adı",
};

function renderTemplate(template: string) {
  const parts = template.split(/(\{\{\w+\}\})/g);
  return parts.map((part, i) => {
    const match = part.match(/^\{\{(\w+)\}\}$/);
    if (match) {
      const label = VARIABLE_LABELS[match[1]] || match[1];
      return (
        <span key={i} className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-accent/15 text-accent text-xs font-medium">
          {label}
        </span>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

export default function ReminderSettingsPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();
  const [loading, setLoading] = useState(true);
  const [configs, setConfigs] = useState<ReminderConfig[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadData = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      const data = await listReminderConfigs(businessId);
      setConfigs(data);
    } catch (err) {
      toast.error("Hatırlatma ayarları yüklenirken hata oluştu.");
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
      if (editingId) {
        await updateReminderConfig(businessId, editingId, form);
        toast.success("Ayar güncellendi.");
      } else {
        await createReminderConfig(businessId, form);
        toast.success("Yeni ayar eklendi.");
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
      title: "Ayarı Sil",
      description: "Bu hatırlatma ayarını silmek istediğinize emin misiniz?",
    });
    if (!ok) return;

    try {
      await deleteReminderConfig(businessId, id);
      toast.success("Ayar silindi.");
      loadData();
    } catch (err) {
      toast.error("Silinirken hata oluştu.");
    }
  };

  const startEdit = (config: ReminderConfig) => {
    setForm({
      channel: config.channel,
      hours_before: config.hours_before,
      message_template: config.message_template,
      is_active: config.is_active,
    });
    setEditingId(config.id);
    setShowForm(true);
  };

  const handleToggleActive = async (config: ReminderConfig) => {
    if (!businessId) return;
    try {
      await updateReminderConfig(businessId, config.id, { is_active: !config.is_active });
      loadData();
    } catch (err) {
      toast.error("Durum güncellenirken hata oluştu.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div
        className="flex flex-wrap items-center justify-between gap-4 border-l-2 pl-3"
        style={{ borderColor: "var(--agent-appointments)" }}
      >
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Randevu Hatırlatmaları</h1>
          <p className="text-sm text-ink-muted">Otomatik hatırlatma mesajlarını yapılandır.</p>
        </div>
        {!showForm && (
          <Button className="gap-2" onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4" />
            Yeni hatırlatma
          </Button>
        )}
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{editingId ? "Hatırlatmayı Düzenle" : "Yeni Hatırlatma"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label>Kanal</Label>
                <Select
                  value={form.channel}
                  onChange={(e) => setForm({ ...form, channel: e.target.value as ReminderChannelType })}
                >
                  <option value="EMAIL">E-posta</option>
                  <option value="SMS">SMS</option>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label>Kaç Saat Önce?</Label>
                <Input
                  type="number"
                  min="1"
                  value={form.hours_before}
                  onChange={(e) => setForm({ ...form, hours_before: parseInt(e.target.value) || 1 })}
                  required
                />
              </div>

              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label>Mesaj Şablonu</Label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  value={form.message_template}
                  onChange={(e) => setForm({ ...form, message_template: e.target.value })}
                  placeholder="Mesaj şablonunuzu yazın..."
                  required
                />
                <div className="flex flex-wrap gap-1.5 mt-1">
                  <span className="text-xs text-ink-muted mr-1">Ekle:</span>
                  {Object.entries(VARIABLE_LABELS).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-[11px] font-medium hover:bg-accent/20 transition-colors cursor-pointer"
                      onClick={() => setForm({ ...form, message_template: form.message_template + `{{${key}}}` })}
                    >
                      + {label}
                    </button>
                  ))}
                </div>
                {form.message_template && (
                  <div className="mt-2 p-3 rounded-md bg-surface border border-border">
                    <p className="text-[11px] text-ink-muted mb-1 font-medium">Önizleme:</p>
                    <p className="text-sm text-ink leading-relaxed">{renderTemplate(form.message_template)}</p>
                  </div>
                )}
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
      ) : configs.length === 0 ? (
        <p className="text-sm text-ink-muted">Kayıtlı hatırlatma ayarı bulunmamaktadır.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {configs.map((config) => (
            <Card key={config.id} className={!config.is_active ? "opacity-60" : ""}>
              <CardContent className="flex flex-col gap-3 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        backgroundColor: "color-mix(in srgb, var(--agent-appointments) 15%, transparent)",
                        color: "var(--agent-appointments)",
                      }}
                    >
                      {config.channel === "EMAIL" ? <Mail className="h-3 w-3" /> : <MessageSquare className="h-3 w-3" />}
                      {config.channel}
                    </span>
                    <span className="text-sm font-medium text-ink flex items-center gap-1">
                      <Bell className="h-3.5 w-3.5" />
                      {config.hours_before} saat önce
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => handleToggleActive(config)} title={config.is_active ? "Devre dışı bırak" : "Aktifleştir"}>
                      <span className={`h-2 w-2 rounded-full ${config.is_active ? 'bg-agent-sales' : 'bg-danger'}`} />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => startEdit(config)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(config.id)}>
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  </div>
                </div>
                
                <div className="rounded-md bg-surface p-3 border border-border">
                  <p className="text-sm text-ink-muted leading-relaxed">{renderTemplate(config.message_template)}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
