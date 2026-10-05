"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { saveTokens } from "@/lib/auth";

/** Same rule as the backend: only same-site relative paths. */
function safeRedirect(path: string | null): string {
  if (!path || !path.startsWith("/") || path.startsWith("//") || path.includes("\\")) {
    return "/select-business";
  }
  return path;
}

/**
 * Landing page after Google sign-in. The backend puts our own tokens in the
 * URL fragment (#...), which is never sent to any server; we store them and
 * remove them from the address bar right away.
 */
export default function GoogleCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    window.history.replaceState(null, "", window.location.pathname);

    if (!access || !refresh) {
      router.replace("/login?error=google_failed");
      return;
    }
    saveTokens(access, refresh);
    router.replace(safeRedirect(params.get("redirect")));
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a1a] text-sm text-gray-400">
      Google ile giriş yapılıyor...
    </div>
  );
}
