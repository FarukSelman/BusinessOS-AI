"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, FileText, Trash2, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  listDocuments,
  uploadDocument,
  uploadTextAsDocument,
  deleteDocument,
  getDocumentStatus,
  getDocumentChunks,
  type BusinessDocument,
  type DocumentStatus,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

const statusStyles: Record<DocumentStatus, { label: string; color: string }> = {
  UPLOADING: { label: "Yükleniyor", color: "var(--ink-muted)" },
  UPLOADED: { label: "Yüklendi", color: "var(--ink-muted)" },
  PROCESSING: { label: "İşleniyor", color: "var(--accent)" },
  READY: { label: "Hazır", color: "var(--agent-sales)" },
  FAILED: { label: "Başarısız", color: "var(--danger)" },
};

// Bu durumlardaki dokümanlar için periyodik olarak durum kontrolü yapılır
const PENDING_STATUSES: DocumentStatus[] = ["UPLOADING", "UPLOADED", "PROCESSING"];

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileTypeInfo(mimeType: string): { label: string; color: string } {
  if (mimeType.includes("pdf")) return { label: "PDF", color: "#ef4444" };
  if (mimeType.includes("word") || mimeType.includes("officedocument"))
    return { label: "DOCX", color: "#2563eb" };
  if (mimeType.includes("text/plain")) return { label: "TXT", color: "#6b7280" };
  return { label: "DOSYA", color: "var(--ink-muted)" };
}

export default function DocumentsPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [documents, setDocuments] = useState<BusinessDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [showInfoForm, setShowInfoForm] = useState(false);
  const [infoText, setInfoText] = useState("");
  const [savingInfo, setSavingInfo] = useState(false);
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({});

  const loadDocuments = useCallback(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    listDocuments(businessId)
      .then(setDocuments)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Dokümanlar yüklenemedi."))
      .finally(() => setLoading(false));
  }, [businessId]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // İşlemdeki dokümanların durumunu 3 saniyede bir kontrol et (READY/FAILED olana kadar)
  useEffect(() => {
    if (!businessId) return;
    const pending = documents.filter((d) => PENDING_STATUSES.includes(d.status));
    if (pending.length === 0) return;

    const interval = setInterval(async () => {
      for (const doc of pending) {
        try {
          const result = await getDocumentStatus(businessId, doc.id);
          setDocuments((prev) =>
            prev.map((d) => (d.id === doc.id ? { ...d, status: result.status } : d))
          );
        } catch {
          // sessizce yut, bir sonraki turda tekrar denenecek
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [documents, businessId]);

    // READY durumundaki dokümanlar için kaç parçaya (chunk) bölündüğünü çek
  useEffect(() => {
    if (!businessId) return;
    const readyDocs = documents.filter((d) => d.status === "READY" && !(d.id in chunkCounts));
    if (readyDocs.length === 0) return;

    readyDocs.forEach((doc) => {
      getDocumentChunks(businessId, doc.id)
        .then((chunks) => {
          setChunkCounts((prev) => ({ ...prev, [doc.id]: chunks.length }));
        })
        .catch(() => {
          // sessizce geç, chunk sayısı gösterilmez
        });
    });
  }, [documents, businessId, chunkCounts]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0 || !businessId) return;
    const file = files[0];
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadDocument(businessId, file);
      setDocuments((prev) => [doc, ...prev]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Doküman yüklenemedi.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleSaveInfo() {
    if (!infoText.trim() || !businessId) return;
    setSavingInfo(true);
    setError(null);
    try {
      const doc = await uploadTextAsDocument(businessId, "kurumsal-bilgiler.txt", infoText.trim());
      setDocuments((prev) => [doc, ...prev]);
      setInfoText("");
      setShowInfoForm(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kaydedilemedi.");
    } finally {
      setSavingInfo(false);
    }
  }


  async function handleDelete(documentId: string) {
    if (!businessId) return;
    const ok = await confirmDialog({
      title: "Dokümanı sil",
      description: "Bu dokümanı silmek istediğine emin misin?",
    });
    if (!ok) return;
    try {
      await deleteDocument(businessId, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Silinemedi.");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Bilgi tabanı</h1>
        <p className="text-sm text-ink-muted">
          Fiyat listeleri, hizmet bilgileri ve SSS dokümanlarını yükle — tüm ajanlar bu bilgileri kullanır.
        </p>
      </div>

      {!showInfoForm ? (
        <Button variant="outline" className="w-fit" onClick={() => setShowInfoForm(true)}>
          Kurumsal bilgi ekle (kuruluş yılı, vizyon, adres vb.)
        </Button>
      ) : (
        <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface-elevated p-4">
          <p className="text-sm font-medium text-ink">Kurumsal bilgiler</p>
          <p className="text-xs text-ink-muted">
            Kuruluş yılı, vizyon, misyon, adres — aklına ne gelirse serbest metin olarak yaz. Ajanlar bunu
            diğer dokümanlar gibi kullanacak.
          </p>
          <textarea
            value={infoText}
            onChange={(e) => setInfoText(e.target.value)}
            rows={6}
            placeholder="Örn: İşletmemiz 2015 yılında kuruldu. Vizyonumuz... Adresimiz..."
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          />
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                setShowInfoForm(false);
                setInfoText("");
              }}
            >
              Vazgeç
            </Button>
            <Button className="flex-1" disabled={savingInfo || !infoText.trim()} onClick={handleSaveInfo}>
              {savingInfo ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </div>
        </div>
      )}

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-colors",
          dragActive ? "border-accent bg-[color-mix(in_srgb,var(--accent)_6%,transparent)]" : "border-border bg-surface-elevated"
        )}
      >
        {uploading ? (
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
        ) : (
          <Upload className="h-8 w-8 text-ink-muted" />
        )}
        <div>
          <p className="text-sm font-medium text-ink">
            {uploading ? "Yükleniyor..." : "Dosyayı sürükle bırak ya da seç"}
          </p>
          <p className="text-xs text-ink-muted">PDF, Word, TXT — işletme dokümanların</p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          Dosya seç
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          accept=".pdf,.doc,.docx,.txt"
        />
      </div>

      {loading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : documents.length === 0 ? (
        <p className="text-sm text-ink-muted">Henüz doküman yok.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {documents.map((d) => {
            const style = statusStyles[d.status];
            const isPending = PENDING_STATUSES.includes(d.status);
            return (
              <Card key={d.id}>
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="flex min-w-0 items-center gap-3">
                    <div
                      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md"
                      style={{ backgroundColor: `color-mix(in srgb, ${getFileTypeInfo(d.mime_type).color} 15%, transparent)` }}
                    >
                      <FileText className="h-5 w-5" style={{ color: getFileTypeInfo(d.mime_type).color }} />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-ink">{d.original_name}</p>
                      <p className="text-xs text-ink-muted">
                        {getFileTypeInfo(d.mime_type).label} · {formatSize(d.file_size)} ·{" "}
                        {new Date(d.created_at).toLocaleDateString("tr-TR")}
                        {chunkCounts[d.id] !== undefined && ` · ${chunkCounts[d.id]} parça`}
                      </p>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span
                      className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                      style={{
                        backgroundColor: `color-mix(in srgb, ${style.color} 15%, transparent)`,
                        color: style.color,
                      }}
                    >
                      {isPending && <Loader2 className="h-3 w-3 animate-spin" />}
                      {d.status === "READY" && <CheckCircle2 className="h-3 w-3" />}
                      {d.status === "FAILED" && <XCircle className="h-3 w-3" />}
                      {style.label}
                    </span>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(d.id)}>
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
