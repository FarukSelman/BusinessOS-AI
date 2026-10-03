"use client";

import { useEffect, useState } from "react";
import { Star, CheckCircle, XCircle, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listReviews,
  getReviewStats,
  approveReview,
  rejectReview,
  replyToReview,
  type CustomerReview,
  type ReviewStats,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export default function ReviewsPage() {
  const businessId = getActiveBusinessId();
  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState<CustomerReview[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const [replyingId, setReplyingId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!businessId) return;
    loadData();
  }, [businessId, statusFilter]);

  async function loadData() {
    if (!businessId) return;
    try {
      const [r, s] = await Promise.all([
        listReviews(businessId, statusFilter === "ALL" ? undefined : statusFilter),
        getReviewStats(businessId),
      ]);
      setReviews(r);
      setStats(s);
    } catch (err) {
      toast.error("Yorumlar yüklenemedi");
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(id: string, action: 'approve' | 'reject') {
    if (!businessId) return;
    setActionLoading(true);
    try {
      if (action === 'approve') await approveReview(businessId, id);
      else await rejectReview(businessId, id);
      toast.success(action === 'approve' ? "Yorum onaylandı" : "Yorum reddedildi");
      loadData();
    } catch (err) {
      toast.error("İşlem başarısız");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReplySubmit(id: string) {
    if (!businessId || !replyText.trim()) return;
    setActionLoading(true);
    try {
      await replyToReview(businessId, id, replyText);
      toast.success("Yanıt eklendi");
      setReplyingId(null);
      setReplyText("");
      loadData();
    } catch (err) {
      toast.error("Yanıt eklenemedi");
    } finally {
      setActionLoading(false);
    }
  }

  function renderStars(rating: number) {
    return Array.from({ length: 5 }).map((_, i) => (
      <Star key={i} className={cn("h-4 w-4", i < rating ? "fill-amber-400 text-amber-400" : "fill-gray-200 text-gray-200")} />
    ));
  }

  if (loading) return <div className="text-sm">Yükleniyor...</div>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[color-mix(in_srgb,var(--agent-sales)_15%,transparent)]">
          <Star className="h-5 w-5 text-[var(--agent-sales)]" />
        </div>
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Müşteri Yorumları</h1>
          <p className="text-sm text-ink-muted">İşletme değerlendirmelerini yönet ve yanıtla.</p>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="col-span-1 md:col-span-1 flex flex-col items-center justify-center p-6 bg-surface">
            <div className="text-5xl font-bold text-ink">{stats.average_rating.toFixed(1)}</div>
            <div className="flex gap-1 mt-2">{renderStars(Math.round(stats.average_rating))}</div>
            <div className="text-sm text-ink-muted mt-2">{stats.total_count} Toplam Yorum</div>
          </Card>
          <Card className="col-span-1 md:col-span-2">
            <CardContent className="p-6">
              <div className="space-y-3">
                {[5, 4, 3, 2, 1].map(r => {
                  const count = stats.rating_distribution[r] || 0;
                  const pct = stats.total_count > 0 ? (count / stats.total_count) * 100 : 0;
                  return (
                    <div key={r} className="flex items-center gap-3 text-sm">
                      <div className="w-8 font-medium">{r} Puan</div>
                      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div className="h-full bg-amber-400 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <div className="w-8 text-right text-ink-muted">{count}</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex gap-2 border-b pb-2">
        {["ALL", "PENDING", "PUBLISHED", "REJECTED"].map(s => {
          const labels: any = { ALL: "Tümü", PENDING: "Bekleyen", PUBLISHED: "Yayınlanan", REJECTED: "Reddedilen" };
          return (
            <button
              key={s}
              className={cn("px-4 py-2 text-sm font-medium rounded-md transition-colors", statusFilter === s ? "bg-[var(--agent-sales)] text-white" : "hover:bg-surface text-ink-muted")}
              onClick={() => setStatusFilter(s)}
            >
              {labels[s]}
            </button>
          );
        })}
      </div>

      <div className="space-y-4">
        {reviews.map(r => (
          <Card key={r.id}>
            <CardContent className="p-5">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-ink">{r.reviewer_name}</span>
                    <span className="text-xs text-ink-muted">{new Date(r.created_at).toLocaleString("tr-TR")}</span>
                    <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-medium border", 
                      r.status === "PUBLISHED" ? "bg-green-50 text-green-700 border-green-200" : 
                      r.status === "REJECTED" ? "bg-red-50 text-red-700 border-red-200" : 
                      "bg-yellow-50 text-yellow-700 border-yellow-200"
                    )}>
                      {r.status === "PUBLISHED" ? "YAYINDA" : r.status === "REJECTED" ? "REDDEDİLDİ" : "BEKLİYOR"}
                    </span>
                  </div>
                  <div className="flex gap-1">{renderStars(r.rating)}</div>
                  {r.comment && <p className="text-sm text-ink mt-2">{r.comment}</p>}
                  
                  {r.reply && (
                    <div className="mt-4 p-3 bg-surface rounded-md border-l-2 border-[var(--agent-sales)]">
                      <div className="text-xs font-semibold text-ink-muted mb-1 flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" /> İşletme Yanıtı
                      </div>
                      <p className="text-sm text-ink">{r.reply}</p>
                    </div>
                  )}

                  {replyingId === r.id && (
                    <div className="mt-3 space-y-2">
                      <textarea 
                        className="w-full text-sm rounded-md border p-2 min-h-[80px]" 
                        placeholder="Müşteriye yanıtınızı yazın..." 
                        value={replyText} 
                        onChange={e => setReplyText(e.target.value)} 
                      />
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => setReplyingId(null)}>Vazgeç</Button>
                        <Button size="sm" disabled={actionLoading} onClick={() => handleReplySubmit(r.id)}>Yanıtı Gönder</Button>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col gap-2 shrink-0">
                  {r.status === "PENDING" && (
                    <>
                      <Button size="sm" variant="outline" className="text-green-600 hover:text-green-700 border-green-200 hover:bg-green-50" onClick={() => handleAction(r.id, 'approve')} disabled={actionLoading}>
                        <CheckCircle className="mr-1.5 h-4 w-4" /> Onayla
                      </Button>
                      <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700 border-red-200 hover:bg-red-50" onClick={() => handleAction(r.id, 'reject')} disabled={actionLoading}>
                        <XCircle className="mr-1.5 h-4 w-4" /> Reddet
                      </Button>
                    </>
                  )}
                  {!r.reply && replyingId !== r.id && (
                    <Button size="sm" variant="outline" onClick={() => setReplyingId(r.id)}>
                      <MessageSquare className="mr-1.5 h-4 w-4" /> Yanıtla
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {reviews.length === 0 && (
          <div className="py-12 text-center text-ink-muted border rounded-lg border-dashed">
            Bu kategoride yorum bulunamadı.
          </div>
        )}
      </div>
    </div>
  );
}
