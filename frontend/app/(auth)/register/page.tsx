"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { register, login, ApiError } from "@/lib/api";
import { AuthDivider, GoogleButton } from "@/components/auth/google-button";

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({ ...form, profile_image: null });
      await login(form.email, form.password);
      const redirect = searchParams.get("redirect");
      router.push(redirect || "/select-business");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kayıt sırasında bir sorun oluştu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0a1a] px-4 py-12 text-white">
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
          <span className="text-gradient">Hesap oluştur</span>
        </h1>
        <p className="mb-8 text-sm text-gray-400">İşletmen için birkaç saniyede kayıt ol.</p>

        <GoogleButton redirect={searchParams.get("redirect")} label="Google ile kayıt ol" />
        <AuthDivider />

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-300">Ad</label>
              <input
                value={form.first_name}
                onChange={(e) => update("first_name", e.target.value)}
                required
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-gray-500 transition-colors focus:border-white/30 focus:outline-none"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-300">Soyad</label>
              <input
                value={form.last_name}
                onChange={(e) => update("last_name", e.target.value)}
                required
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-gray-500 transition-colors focus:border-white/30 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">E-posta</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              required
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-gray-500 transition-colors focus:border-white/30 focus:outline-none"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">Şifre</label>
            <input
              type="password"
              minLength={8}
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
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
            {loading ? "Kayıt olunuyor..." : "Kayıt ol"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-400">
          Zaten hesabın var mı?{" "}
          <Link
            href={
              searchParams.get("redirect")
                ? `/login?redirect=${encodeURIComponent(searchParams.get("redirect")!)}`
                : "/login"
            }
            className="font-medium text-white underline"
          >
            Giriş yap
          </Link>
        </p>
      </div>
    </div>
  );
}