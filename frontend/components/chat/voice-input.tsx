"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError, getVoiceStatus, transcribeAudio, type VoiceStatus } from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";

type Phase = "idle" | "listening" | "processing";

// Sunucunun kabul ettiği biçimler; tarayıcının desteklediği ilki seçilir (Safari: mp4).
const MIME_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

// İşletme başına bir kez sorulur.
const statusCache = new Map<string, Promise<VoiceStatus>>();

function browserProblem(): string | null {
  if (typeof window === "undefined") return null;
  if (!window.isSecureContext) return "Mikrofon yalnızca güvenli bağlantıda (HTTPS) kullanılabilir.";
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    return "Bu tarayıcı ses kaydını desteklemiyor.";
  }
  return null;
}

function micErrorMessage(err: unknown): string {
  const name = err instanceof DOMException ? err.name : "";
  if (name === "NotAllowedError" || name === "SecurityError") {
    return "Mikrofon izni verilmedi. Tarayıcının adres çubuğundaki izin ayarından mikrofona izin verin.";
  }
  if (name === "NotFoundError" || name === "OverconstrainedError") return "Mikrofon bulunamadı.";
  if (name === "NotReadableError") return "Mikrofon başka bir uygulama tarafından kullanılıyor.";
  return "Mikrofon başlatılamadı.";
}

/**
 * Sohbet için sesli giriş: kaydı başlat/durdur, metne çevir, metni çağırana ver
 * (kullanıcı kontrol edip gönderir, otomatik gönderim yok). Esc kaydı iptal eder.
 */
export function useVoiceInput(onTranscript: (text: string) => void) {
  const businessId = getActiveBusinessId();
  const [phase, setPhase] = useState<Phase>("idle");
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<VoiceStatus | null>(null);
  const [problem] = useState(browserProblem);

  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const cancelled = useRef(false);
  const timer = useRef<number | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
  });

  useEffect(() => {
    if (!businessId || problem) return;
    let request = statusCache.get(businessId);
    if (!request) {
      request = getVoiceStatus(businessId);
      statusCache.set(businessId, request);
      request.catch(() => statusCache.delete(businessId));
    }
    let active = true;
    request.then((s) => active && setStatus(s)).catch(() => {});
    return () => {
      active = false;
    };
  }, [businessId, problem]);

  const release = useCallback(() => {
    if (timer.current !== null) window.clearInterval(timer.current);
    timer.current = null;
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
    recorder.current = null;
  }, []);

  useEffect(() => release, [release]);

  const finish = useCallback(async () => {
    const type = recorder.current?.mimeType || chunks.current[0]?.type || "audio/webm";
    release();
    if (cancelled.current) {
      setPhase("idle");
      return;
    }
    const blob = new Blob(chunks.current, { type });
    chunks.current = [];
    if (blob.size === 0 || !businessId) {
      setPhase("idle");
      setError("Ses kaydı boş; lütfen tekrar deneyin.");
      return;
    }
    setPhase("processing");
    try {
      onTranscriptRef.current(await transcribeAudio(businessId, blob));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ses metne çevrilemedi; lütfen tekrar deneyin.");
    } finally {
      setPhase("idle");
    }
  }, [businessId, release]);

  const stop = useCallback(() => {
    if (recorder.current?.state === "recording") recorder.current.stop();
  }, []);

  const start = useCallback(async () => {
    setError(null);
    cancelled.current = false;
    let media: MediaStream;
    try {
      media = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setError(micErrorMessage(err));
      return;
    }
    const mimeType = MIME_TYPES.find((t) => MediaRecorder.isTypeSupported(t));
    // Konuşma için 32 kbps yeterli: 60 sn yaklaşık 240 KB (tarayıcı varsayılanı ~128 kbps).
    const rec = new MediaRecorder(media, { audioBitsPerSecond: 32_000, ...(mimeType ? { mimeType } : {}) });
    stream.current = media;
    recorder.current = rec;
    chunks.current = [];
    rec.ondataavailable = (e) => e.data.size > 0 && chunks.current.push(e.data);
    rec.onstop = () => void finish();
    rec.start(250);
    setSeconds(0);
    setPhase("listening");
    const limit = status?.max_seconds ?? 60;
    const startedAt = Date.now();
    timer.current = window.setInterval(() => {
      const s = Math.floor((Date.now() - startedAt) / 1000);
      setSeconds(s);
      if (s >= limit) stop();  // süre sınırı: kaydı kendiliğinden bitir
    }, 250);
  }, [finish, status, stop]);

  const cancel = useCallback(() => {
    cancelled.current = true;
    stop();
  }, [stop]);

  // Esc: kayıt sürerken iptal (metne çevirmeden)
  useEffect(() => {
    if (phase !== "listening") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        cancel();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [phase, cancel]);

  const disabledReason = problem ?? (status && !status.enabled ? status.reason ?? "Sesli komut kullanılamıyor." : null);

  return {
    phase,
    seconds,
    error,
    disabledReason,
    ready: status !== null || problem !== null,
    toggle: () => (phase === "listening" ? stop() : phase === "idle" ? void start() : undefined),
    clearError: () => setError(null),
  };
}

export type VoiceInput = ReturnType<typeof useVoiceInput>;

export function VoiceButton({ voice, disabled }: { voice: VoiceInput; disabled?: boolean }) {
  const listening = voice.phase === "listening";
  const processing = voice.phase === "processing";
  const label = voice.disabledReason
    ? `Sesli komut kullanılamıyor: ${voice.disabledReason}`
    : listening
      ? "Kaydı durdur ve metne çevir"
      : processing
        ? "Ses metne çevriliyor"
        : "Sesle yaz: kaydı başlat";
  return (
    <Button
      type="button"
      size="icon"
      variant={listening ? "default" : "outline"}
      className={cn(
        "relative h-11 w-11 shrink-0 sm:h-10 sm:w-10",  // telefonda 44 px dokunma alanı
        listening && "bg-danger-solid text-white ring-2 ring-danger ring-offset-2 ring-offset-surface hover:brightness-110"
      )}
      onClick={voice.toggle}
      disabled={disabled || processing || !voice.ready || !!voice.disabledReason}
      aria-pressed={listening}
      aria-label={label}
      title={label}
    >
      {processing ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      ) : listening ? (
        <>
          <Square className="h-4 w-4 fill-current" aria-hidden />
          <span className="absolute -inset-1 animate-ping rounded-md border-2 border-danger opacity-60" aria-hidden />
        </>
      ) : (
        <Mic className="h-4 w-4" aria-hidden />
      )}
    </Button>
  );
}

/** Durum satırı: metin + ikon (renk tek başına bilgi taşımaz), ekran okuyucuya duyurulur. */
export function VoiceStatusLine({ voice }: { voice: VoiceInput }) {
  const time = `${Math.floor(voice.seconds / 60)}:${String(voice.seconds % 60).padStart(2, "0")}`;
  return (
    <div className="px-4 pb-2 text-sm">
      <p aria-live="polite" className="text-ink-muted">
        {voice.phase === "listening" && (
          <span className="flex items-center gap-2 text-ink">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-danger" aria-hidden />
            Dinleniyor {time} — durdurmak için mikrofon butonuna basın, iptal için Esc.
          </span>
        )}
        {voice.phase === "processing" && "Ses metne çevriliyor…"}
      </p>
      {voice.error && (
        <p role="alert" className="mt-1 text-danger">
          {voice.error}
        </p>
      )}
      {voice.disabledReason && voice.phase === "idle" && !voice.error && (
        <p className="mt-1 text-xs text-ink-muted">Sesli komut kapalı: {voice.disabledReason}</p>
      )}
    </div>
  );
}
