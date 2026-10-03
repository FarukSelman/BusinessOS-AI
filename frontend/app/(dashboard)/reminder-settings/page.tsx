"use client";

import React, { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Bell, Mail, MessageSquare, Send, History, RefreshCw } from "lucide-react";
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
  listReminderLogs,
  sendTestReminder,
  ApiError,
  ReminderLog,
  ReminderStatusType,
  ReminderConfig,
  ReminderChannelType
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

const emptyForm = {
  channel: "EMAIL" as ReminderChannelType,
  hours_before: 24,
  message_template:
    "Sayın {{customer_name}}, {{appointment_date}} saat {{start_time}}'da {{business_name}} işletmesinde {{service_name}} randevunuz bulunmaktadır.",
  is_active: true,
};

const VARIABLE_LABELS: Record<string, string> = {
  customer_name: "Müşteri Adı",
  appointment_date: "Randevu Tarihi",
  start_time: "Başlangıç Saati",
  service_name: "Hizmet Adı",
  staff_name: "Personel",
  business_name: "İşletme Adı",
  branch_name: "Şube Adı",
  branch_address: "Şube Adresi",
};

const STATUS_STYLES: Record<ReminderStatusType, { label: string; className: string }> = {
  SENT: { label: "Gönderildi", className: "bg-agent-sales/15 text-agent-sales" },
  FAILED: { label: "Başarısız", className: "bg-danger/15 text-danger" },
  SKIPPED: { label: "Atlandı", className: "bg-ink-muted/15 text-ink-muted" },
  PENDING: { label: "Gönderiliyor", className: "bg-accent/15 text-accent" },
};

const LOG_PAGE_SIZE = 20;

function formatDateTime(value: string | null) {
  if (!value) return "—";
  // Backend times are naive local (APP_TIMEZONE) values; show them as-is.
  const d = new Date(value.replace(/Z$/, ""));
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
  const [testingId, setTestingId] = useState<string | null>(null);
  const [logs, setLogs] = useState<ReminderLog[]>([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logPage, setLogPage] = useState(1);

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

  const loadLogs = async (page: number = logPage) => {
    if (!businessId) return;
    setLogsLoading(true);
    try {
      const data = await listReminderLogs(businessId, { page, size: LOG_PAGE_SIZE });
      setLogs(data);
      setLogPage(page);
    } catch (err) {
      toast.error("Gönderim geçmişi yüklenirken hata oluştu.");
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    loadLogs(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId]);

  const handleSendTest = async (config: ReminderConfig) => {
    if (!businessId) return;
    setTestingId(config.id);
    try {
      const res = await sendTestReminder(businessId, config.id);
      toast.success(`Test e-postası ${res.recipient} adresine gönderildi.`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Test e-postası gönderilemedi.");
    } finally {
      setTestingId(null);
    }
  };

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
                  <option value="SMS" disabled>
                    SMS (Yakında)
                  </option>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label>Kaç Saat Önce?</Label>
                <Input
                  type="number"
                  min="1"
                  max="168"
                  value={form.hours_before}
                  onChange={(e) =>
                    setForm({ ...form, hours_before: Math.min(168, Math.max(1, parseInt(e.target.value) || 1)) })
                  }
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
                  maxLength={2000}
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
                    {config.channel === "EMAIL" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleSendTest(config)}
                        disabled={testingId === config.id}
                        title="Kendi e-posta adresime test gönder"
                      >
                        <Send className={`h-4 w-4 ${testingId === config.id ? "animate-pulse" : ""}`} />
                      </Button>
                    )}
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

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="h-4 w-4" />
            Gönderim geçmişi
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={() => loadLogs(logPage)} title="Yenile">
            <RefreshCw className={`h-4 w-4 ${logsLoading ? "animate-spin" : ""}`} />
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {logsLoading && logs.length === 0 ? (
            <p className="text-sm text-ink-muted">Yükleniyor...</p>
          ) : logs.length === 0 ? (
            <p className="text-sm text-ink-muted">
              {logPage === 1 ? "Henüz gönderilmiş bir hatırlatma yok." : "Bu sayfada kayıt yok."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-ink-muted">
                    <th className="py-2 pr-3 font-medium">Durum</th>
                    <th className="py-2 pr-3 font-medium">Müşteri</th>
                    <th className="py-2 pr-3 font-medium">Randevu</th>
                    <th className="py-2 pr-3 font-medium">Kural</th>
                    <th className="py-2 pr-3 font-medium">Gönderim</th>
                    <th className="py-2 font-medium">Açıklama</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => {
                    const st = STATUS_STYLES[log.status] ?? STATUS_STYLES.PENDING;
                    return (
                      <tr key={log.id} className="border-b border-border/60 align-top last:border-0">
                        <td className="py-2 pr-3">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${st.className}`}>
                            {st.label}
                          </span>
                        </td>
                        <td className="py-2 pr-3">
                          <div className="text-ink">{log.customer_name || "—"}</div>
                          {log.recipient_email && (
                            <div className="text-xs text-ink-muted">{log.recipient_email}</div>
                          )}
                        </td>
                        <td className="whitespace-nowrap py-2 pr-3 text-ink">{formatDateTime(log.appointment_start)}</td>
                        <td className="whitespace-nowrap py-2 pr-3 text-ink-muted">
                          {log.hours_before != null ? `${log.hours_before} saat önce` : "—"}
                        </td>
                        <td className="whitespace-nowrap py-2 pr-3 text-ink-muted">{formatDateTime(log.sent_at)}</td>
                        <td className="py-2 text-xs text-ink-muted">
                          {log.error_message || "—"}
                          {log.status === "FAILED" && log.attempts > 0 && (
                            <span className="ml-1">({log.attempts}. deneme)</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {(logPage > 1 || logs.length === LOG_PAGE_SIZE) && (
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={logPage <= 1 || logsLoading}
                onClick={() => loadLogs(logPage - 1)}
              >
                Önceki
              </Button>
              <span className="text-xs text-ink-muted">Sayfa {logPage}</span>
              <Button
                variant="outline"
                size="sm"
                disabled={logs.length < LOG_PAGE_SIZE || logsLoading}
                onClick={() => loadLogs(logPage + 1)}
              >
                Sonraki
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
