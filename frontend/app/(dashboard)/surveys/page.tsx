"use client";

import { useEffect, useState } from "react";
import { ClipboardList, Plus, BarChart2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listSurveys,
  createSurvey,
  deleteSurvey,
  getSurveyResponses,
  type Survey,
  type SurveyResponseItem,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

export default function SurveysPage() {
  const businessId = getActiveBusinessId();
  const confirmDialog = useConfirm();
  const [loading, setLoading] = useState(true);
  const [surveys, setSurveys] = useState<Survey[]>([]);

  // Survey Form
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", is_auto_send: false });
  const [questions, setQuestions] = useState<{ type: string; text: string; options: string; required: boolean }[]>([]);
  const [saving, setSaving] = useState(false);

  // Detail View
  const [selectedSurvey, setSelectedSurvey] = useState<Survey | null>(null);
  const [responses, setResponses] = useState<SurveyResponseItem[]>([]);
  const [responsesLoading, setResponsesLoading] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    loadSurveys();
  }, [businessId]);

  async function loadSurveys() {
    if (!businessId) return;
    try {
      const s = await listSurveys(businessId);
      setSurveys(s);
    } catch (err) {
      toast.error("Anketler yüklenemedi");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewResponses(s: Survey) {
    if (!businessId) return;
    setSelectedSurvey(s);
    setResponsesLoading(true);
    try {
      const res = await getSurveyResponses(businessId, s.id);
      setResponses(res);
    } catch (err) {
      toast.error("Yanıtlar yüklenemedi");
    } finally {
      setResponsesLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId) return;
    if (questions.length === 0) return toast.error("En az bir soru eklemelisiniz.");
    setSaving(true);
    try {
      const formattedQuestions = questions.map(q => ({
        type: q.type,
        text: q.text,
        required: q.required,
        options: q.type === "MULTIPLE_CHOICE" ? q.options.split(",").map(o => o.trim()).filter(Boolean) : null,
      }));
      await createSurvey(businessId, {
        ...form,
        questions: formattedQuestions,
      });
      toast.success("Anket oluşturuldu");
      setShowForm(false);
      setForm({ title: "", description: "", is_auto_send: false });
      setQuestions([]);
      loadSurveys();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Oluşturulamadı");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Anketi Sil",
      description: "Bu anketi silmek istediğinize emin misiniz?",
    });
    if (!ok) return;
    try {
      await deleteSurvey(businessId, id);
      toast.success("Anket silindi");
      loadSurveys();
      if (selectedSurvey?.id === id) setSelectedSurvey(null);
    } catch (err) {
      toast.error("Silinemedi");
    }
  }

  function addQuestion() {
    setQuestions([...questions, { type: "RATING", text: "", options: "", required: false }]);
  }

  if (loading) return <div className="text-sm">Yükleniyor...</div>;

  if (selectedSurvey) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => setSelectedSurvey(null)}>Geri Dön</Button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink">{selectedSurvey.title}</h1>
            <p className="text-sm text-ink-muted">Yanıtlar ve İstatistikler</p>
          </div>
        </div>
        
        {responsesLoading ? (
          <p className="text-sm">Yükleniyor...</p>
        ) : (
          <div className="grid gap-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-6">
                  <p className="text-sm text-ink-muted">Toplam Yanıt</p>
                  <p className="text-3xl font-bold">{responses.length}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <p className="text-sm text-ink-muted">Ortalama Puan</p>
                  <p className="text-3xl font-bold text-[var(--agent-marketing)]">
                    {responses.filter(r => r.overall_rating).length > 0 
                      ? (responses.filter(r => r.overall_rating).reduce((a, b) => a + (b.overall_rating || 0), 0) / responses.filter(r => r.overall_rating).length).toFixed(1)
                      : "-"}
                  </p>
                </CardContent>
              </Card>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>Yanıt Listesi</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {responses.map(r => (
                    <div key={r.id} className="border rounded-lg p-4 bg-surface space-y-3">
                      <div className="flex justify-between items-center border-b pb-2">
                        <div>
                          <p className="font-medium">{r.respondent_name || "İsimsiz Müşteri"}</p>
                          <p className="text-xs text-ink-muted">{new Date(r.created_at).toLocaleString("tr-TR")}</p>
                        </div>
                        {r.overall_rating && (
                          <div className="font-bold text-[var(--agent-marketing)]">{r.overall_rating} / 5</div>
                        )}
                      </div>
                      <div className="space-y-2">
                        {r.answers.map((a: any, i) => {
                          const q = selectedSurvey.questions.find((x: any) => x.id === a.question_id);
                          return (
                            <div key={i} className="text-sm">
                              <span className="font-medium text-ink">{q?.text || "Soru"}: </span>
                              <span className="text-ink-muted">{String(a.answer)}</span>
                            </div>
                          );
                        })}
                      </div>
                      {r.comment && (
                        <div className="text-sm italic mt-2 text-ink-muted">"{r.comment}"</div>
                      )}
                    </div>
                  ))}
                  {responses.length === 0 && <p className="text-sm text-ink-muted">Henüz yanıt yok.</p>}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[color-mix(in_srgb,var(--agent-marketing)_15%,transparent)]">
            <ClipboardList className="h-5 w-5 text-[var(--agent-marketing)]" />
          </div>
          <div>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Memnuniyet Anketleri</h1>
            <p className="text-sm text-ink-muted">Müşteri geri bildirimlerini topla ve analiz et.</p>
          </div>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)} className="bg-[var(--agent-marketing)] text-white hover:bg-[var(--agent-marketing)]/90">
            <Plus className="mr-2 h-4 w-4" /> Yeni Anket
          </Button>
        )}
      </div>

      {showForm && (
        <Card className="border-[var(--agent-marketing)]/20 shadow-md">
          <CardHeader>
            <CardTitle>Yeni Anket Oluştur</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5 col-span-2">
                  <Label>Anket Başlığı</Label>
                  <Input required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
                </div>
                <div className="space-y-1.5 col-span-2">
                  <Label>Açıklama (Opsiyonel)</Label>
                  <Input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
                </div>
                <div className="flex items-center gap-2 col-span-2">
                  <input type="checkbox" className="rounded border-gray-300" checked={form.is_auto_send} onChange={e => setForm({ ...form, is_auto_send: e.target.checked })} />
                  <Label>Randevulardan sonra otomatik gönder</Label>
                </div>
              </div>
              
              <div className="space-y-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <Label className="text-base font-semibold">Sorular</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addQuestion}>
                    Soru Ekle
                  </Button>
                </div>
                
                {questions.map((q, i) => (
                  <div key={i} className="flex gap-4 p-4 border rounded-md bg-surface relative group">
                    <Button type="button" variant="ghost" size="icon" className="absolute top-2 right-2 text-danger opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => setQuestions(questions.filter((_, idx) => idx !== i))}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    <div className="grid grid-cols-2 gap-3 w-full">
                      <div className="space-y-1.5 col-span-2 md:col-span-1">
                        <Label>Soru Tipi</Label>
                        <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={q.type} onChange={e => { const n = [...questions]; n[i].type = e.target.value; setQuestions(n); }}>
                          <option value="RATING">Puanlama (1-5)</option>
                          <option value="TEXT">Metin Yanıtı</option>
                          <option value="YES_NO">Evet/Hayır</option>
                          <option value="MULTIPLE_CHOICE">Çoktan Seçmeli</option>
                        </select>
                      </div>
                      <div className="space-y-1.5 col-span-2 md:col-span-1 flex items-center mt-6">
                        <input type="checkbox" className="mr-2" checked={q.required} onChange={e => { const n = [...questions]; n[i].required = e.target.checked; setQuestions(n); }} />
                        <Label>Zorunlu Alan</Label>
                      </div>
                      <div className="space-y-1.5 col-span-2">
                        <Label>Soru Metni</Label>
                        <Input required value={q.text} onChange={e => { const n = [...questions]; n[i].text = e.target.value; setQuestions(n); }} />
                      </div>
                      {q.type === "MULTIPLE_CHOICE" && (
                        <div className="space-y-1.5 col-span-2">
                          <Label>Seçenekler (Virgülle ayırın)</Label>
                          <Input required placeholder="Seçenek 1, Seçenek 2" value={q.options} onChange={e => { const n = [...questions]; n[i].options = e.target.value; setQuestions(n); }} />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {questions.length === 0 && <p className="text-sm text-ink-muted text-center py-4">Soru eklemek için "Soru Ekle" butonuna tıklayın.</p>}
              </div>
              
              <div className="flex gap-2 justify-end pt-4">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Vazgeç</Button>
                <Button type="submit" disabled={saving} className="bg-[var(--agent-marketing)] text-white">Kaydet</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {surveys.map(s => (
          <Card key={s.id} className="group hover:border-[var(--agent-marketing)]/50 transition-colors">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-base font-semibold">{s.title}</CardTitle>
                <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-medium", 
                  s.status === "ACTIVE" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                )}>
                  {s.status === "ACTIVE" ? "AKTİF" : "PASİF"}
                </span>
              </div>
              {s.description && <p className="text-xs text-ink-muted line-clamp-2">{s.description}</p>}
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-ink-muted mb-4 mt-2">
                <div className="flex items-center gap-1">
                  <BarChart2 className="h-4 w-4" />
                  <span>{s.questions.length} Soru</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => handleViewResponses(s)}>
                  Yanıtlar
                </Button>
                <Button variant="ghost" size="icon" className="text-danger" onClick={() => handleDelete(s.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {surveys.length === 0 && !showForm && (
          <div className="col-span-full py-12 text-center text-ink-muted border rounded-lg border-dashed">
            Anket bulunamadı. Yeni anket oluşturarak başlayın.
          </div>
        )}
      </div>
    </div>
  );
}
