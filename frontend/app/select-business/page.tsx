"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import {
  getBusinesses,
  createBusiness,
  type Business,
  ApiError,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { saveActiveBusinessId } from "@/lib/business";
import { Building2, Plus, Sparkles, ArrowRight, Briefcase, Mail, Phone, Tag } from "lucide-react";

export default function SelectBusinessPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }

    getBusinesses()
      .then((data) => {
        setBusinesses(data);
        setShowCreateForm(data.length === 0);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "İşletmeler yüklenemedi.");
      })
      .finally(() => setLoading(false));
  }, [router]);

  function selectBusiness(business: Business) {
    saveActiveBusinessId(business.id);
    router.push("/dashboard");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a1a]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <p className="text-sm text-gray-400">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a1a] px-4 py-12 relative overflow-hidden text-white">
      {/* Background decorations */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-accent/[0.06] blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-purple-500/[0.06] blur-3xl" />
        <div className="absolute top-1/3 left-0 w-[300px] h-[300px] rounded-full bg-blue-500/[0.04] blur-3xl" />
      </div>

      <div className="w-full max-w-lg relative z-10">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 border border-accent/10 mb-4">
            <Sparkles className="h-6 w-6 text-accent" />
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-white">
            İşletme Seç
          </h1>
          <p className="mt-2 text-sm text-gray-400 max-w-sm mx-auto">
            Devam etmek için bir işletme seçin ya da yeni bir işletme oluşturun.
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        {/* Business list */}
        {businesses.length > 0 && (
          <div className="mb-6 flex flex-col gap-3">
            {businesses.map((b, i) => (
              <button
                key={b.id}
                onClick={() => selectBusiness(b)}
                className="group flex items-center gap-4 rounded-xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-4 text-left transition-all duration-200 hover:border-accent/40 hover:bg-white/[0.08] hover:shadow-lg hover:shadow-accent/5 hover:-translate-y-0.5"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent/15 to-accent/5 border border-accent/10 transition-all group-hover:from-accent/25 group-hover:to-accent/10">
                  <Building2 className="h-5 w-5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate">{b.name}</p>
                  <p className="text-sm text-gray-400 truncate">{b.industry || "İşletme"}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-gray-500 transition-all group-hover:text-accent group-hover:translate-x-1" />
              </button>
            ))}
          </div>
        )}

        {businesses.length === 0 && (
          <div className="mb-6 rounded-xl bg-white/[0.04] border border-white/10 p-6 text-center">
            <Building2 className="h-8 w-8 text-gray-500 mx-auto mb-3 opacity-50" />
            <p className="text-sm text-gray-400">
              Henüz bir işletmeniz yok. Bir davetin mi var? Sana gönderilen davet linkine tıklayarak katılabilirsin.
              Yoksa aşağıdan yeni bir işletme oluşturabilirsin.
            </p>
          </div>
        )}

        {/* Create form toggle / form */}
        {!showCreateForm ? (
          <Button
            variant="outline"
            className="w-full gap-2 h-12 rounded-xl border-dashed border-white/20 text-gray-300 hover:border-accent/40 hover:bg-accent/5 hover:text-white transition-all"
            onClick={() => setShowCreateForm(true)}
          >
            <Plus className="h-4 w-4" />
            Yeni işletme oluştur
          </Button>
        ) : (
          <CreateBusinessForm
            onCreated={(business) => {
              saveActiveBusinessId(business.id);
              router.push("/dashboard");
            }}
            onCancel={businesses.length > 0 ? () => setShowCreateForm(false) : undefined}
          />
        )}
      </div>
    </div>
  );
}

function CreateBusinessForm({
  onCreated,
  onCancel,
}: {
  onCreated: (business: Business) => void;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState({ name: "", industry: "", email: "", phone: "" });
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
      const business = await createBusiness(form);
      onCreated(business);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "İşletme oluşturulamadı.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="bg-white/[0.05] backdrop-blur-sm border-white/10 rounded-xl overflow-hidden">
      <div className="h-1 w-full bg-gradient-to-r from-accent via-purple-500 to-accent" />
      <CardHeader className="pb-4">
        <CardTitle className="text-lg flex items-center gap-2 text-white">
          <Building2 className="h-5 w-5 text-accent" />
          Yeni İşletme
        </CardTitle>
        <CardDescription className="text-gray-400">İşletmenizin temel bilgilerini girin.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name" className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
              <Briefcase className="h-3.5 w-3.5" /> İşletme Adı
            </Label>
            <Input
              id="name"
              placeholder="Örn. Güzellik Salonu"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              required
              className="h-10 rounded-lg bg-white/[0.06] border-white/10 text-white placeholder:text-gray-500 focus:border-accent"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="industry" className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
              <Tag className="h-3.5 w-3.5" /> Sektör
            </Label>
            <Input
              id="industry"
              placeholder="Örn. Kuaför, Restoran, Danışmanlık"
              value={form.industry}
              onChange={(e) => update("industry", e.target.value)}
              required
              className="h-10 rounded-lg bg-white/[0.06] border-white/10 text-white placeholder:text-gray-500 focus:border-accent"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="biz-email" className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
                <Mail className="h-3.5 w-3.5" /> E-posta
              </Label>
              <Input
                id="biz-email"
                type="email"
                placeholder="info@isletme.com"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
                className="h-10 rounded-lg bg-white/[0.06] border-white/10 text-white placeholder:text-gray-500 focus:border-accent"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="phone" className="flex items-center gap-1.5 text-xs font-medium text-gray-400">
                <Phone className="h-3.5 w-3.5" /> Telefon
              </Label>
              <Input
                id="phone"
                placeholder="0555 123 45 67"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                required
                className="h-10 rounded-lg bg-white/[0.06] border-white/10 text-white placeholder:text-gray-500 focus:border-accent"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex gap-2 pt-2">
            {onCancel && (
              <Button type="button" variant="outline" className="flex-1 h-10 rounded-lg" onClick={onCancel}>
                Vazgeç
              </Button>
            )}
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 h-10 rounded-lg bg-accent hover:bg-accent/90 text-white"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Oluşturuluyor...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Oluştur
                </span>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
