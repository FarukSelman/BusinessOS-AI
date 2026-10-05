"use client";

import { googleLoginUrl } from "@/lib/api";

type Props = {
  /** Relative path to open after sign-in (e.g. an invitation link). */
  redirect?: string | null;
  label?: string;
};

/**
 * Full-page navigation to the backend, which redirects to Google's account
 * picker. A plain link (not fetch) is required for the OAuth redirect flow.
 */
export function GoogleButton({ redirect, label = "Google ile devam et" }: Props) {
  return (
    <a
      href={googleLoginUrl(redirect)}
      className="flex w-full items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
    >
      <span
        aria-hidden
        className="flex h-5 w-5 items-center justify-center rounded-full bg-white text-[11px] font-bold text-gray-900"
      >
        G
      </span>
      {label}
    </a>
  );
}

export function AuthDivider() {
  return (
    <div className="my-5 flex items-center gap-3 text-xs text-gray-500">
      <span className="h-px flex-1 bg-white/10" />
      veya
      <span className="h-px flex-1 bg-white/10" />
    </div>
  );
}

const GOOGLE_ERRORS: Record<string, string> = {
  google_cancelled: "Google ile giriş iptal edildi.",
  google_state: "Oturum doğrulanamadı (süre dolmuş olabilir). Lütfen tekrar dene.",
  google_email_not_verified: "Google hesabının e-posta adresi doğrulanmamış.",
  google_account_inactive: "Bu e-postaya bağlı hesap pasif durumda. Yöneticinle iletişime geç.",
  google_not_configured: "Google ile giriş bu sunucuda henüz yapılandırılmamış.",
  google_network: "Google'a ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.",
};

export function googleErrorMessage(code: string | null): string | null {
  if (!code || !code.startsWith("google_")) return null;
  return GOOGLE_ERRORS[code] ?? "Google ile giriş yapılamadı. Lütfen tekrar dene.";
}
