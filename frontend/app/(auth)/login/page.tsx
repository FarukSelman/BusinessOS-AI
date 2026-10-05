"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { login, ApiError } from "@/lib/api";
import { AuthDivider, GoogleButton, googleErrorMessage } from "@/components/auth/google-button";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(() => googleErrorMessage(searchParams.get("error")));
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      const redirect = searchParams.get("redirect");
      router.push(redirect || "/select-business");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Bir şeyler ters gitti, tekrar dene.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0a1a] px-4 text-white">
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="bg-grid absolute inset-0" />

      <div className="glass-card relative z-10 w-full max-w-sm rounded-2xl p-8">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-1 text-sm text-gray-400 transition-colors hover:text-white"
        >
          ← Ana sayfaya dön
        </Link>

        <h1 className="font-display mb-2 text-2xl font-bold">
          <span className="text-gradient">Giriş yap</span>
        </h1>
        <p className="mb-8 text-sm text-gray-400">İşletme panelinize erişmek için giriş yapın.</p>

        <GoogleButton redirect={searchParams.get("redirect")} />
        <AuthDivider />

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">E-posta</label>
            <input
              type="email"
              placeholder="ornek@sirket.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-gray-500 transition-colors focus:border-white/30 focus:outline-none"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">Şifre</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-gray-500 transition-colors focus:border-white/30 focus:outline-none"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Giriş yapılıyor..." : "Giriş yap"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-400">
          Hesabın yok mu?{" "}
          <Link
            href={
              searchParams.get("redirect")
                ? `/register?redirect=${encodeURIComponent(searchParams.get("redirect")!)}`
                : "/register"
            }
            className="font-medium text-white underline"
          >
            Kayıt ol
          </Link>
        </p>
      </div>
    </div>
  );
}