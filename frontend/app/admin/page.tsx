"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Trash2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmDialogProvider, useConfirm } from "@/components/providers/confirm-dialog-provider";
import {
  getMe,
  adminListBusinesses,
  adminUpdateBusinessStatus,
  adminUpdateBusinessPlan,
  adminDeleteBusiness,
  type AdminBusiness,
  ApiError,
} from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

export default function AdminPage() {
  return (
    <ConfirmDialogProvider>
      <AdminPageContent />
    </ConfirmDialogProvider>
  );
}

function AdminPageContent() {
  const router = useRouter();
  const confirmDialog = useConfirm();

  const [checking, setChecking] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const [businesses, setBusinesses] = useState<AdminBusiness[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login?redirect=/admin");
      return;
    }
    getMe()
      .then((me) => {
        setAuthorized(me.is_superadmin);
        setChecking(false);
        if (me.is_superadmin) {
          adminListBusinesses()
            .then(setBusinesses)
            .catch((err) => toast.error(err instanceof ApiError ? err.message : "Yüklenemedi."))
            .finally(() => setLoading(false));
        } else {
          setLoading(false);
        }
      })
      .catch(() => {
        setChecking(false);
        setLoading(false);
      });
  }, [router]);

  async function handleStatusChange(business: AdminBusiness, status: AdminBusiness["status"]) {
    try {
      const updated = await adminUpdateBusinessStatus(business.id, status);
      setBusinesses((prev) => prev.map((b) => (b.id === business.id ? updated : b)));
      toast.success("Durum güncellendi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Güncellenemedi.");
    }
  }

  async function handlePlanChange(business: AdminBusiness, plan: AdminBusiness["plan"]) {
    try {
      const updated = await adminUpdateBusinessPlan(business.id, plan);
      setBusinesses((prev) => prev.map((b) => (b.id === business.id ? updated : b)));
      toast.success("Plan güncellendi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Güncellenemedi.");
    }
  }

  async function handleDelete(business: AdminBusiness) {
    const ok = await confirmDialog({
      title: "İşletmeyi sil",
      description: `"${business.name}" işletmesini kalıcı olarak silmek istediğine emin misin?`,
    });
    if (!ok) return;
    try {
      await adminDeleteBusiness(business.id);
      setBusinesses((prev) => prev.filter((b) => b.id !== business.id));
      toast.success("İşletme silindi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Silinemedi.");
    }
  }

  if (checking) {
    return <div className="flex min-h-screen items-center justify-center bg-surface text-sm text-ink-muted">Kontrol ediliyor...</div>;
  }

  if (!authorized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface px-4">
        <Card className="w-full max-w-sm">
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <ShieldCheck className="h-8 w-8 text-danger" />
            <p className="font-medium text-ink">Bu sayfaya erişim yetkin yok.</p>
            <p className="text-sm text-ink-muted">Platform admin yetkisi gerekiyor.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-accent" />
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">
            Platform Admin
          </h1>
        </div>

        {loading ? (
          <p className="text-sm text-ink-muted">Yükleniyor...</p>
        ) : (
          <div className="flex flex-col gap-3">
            {businesses.map((b) => (
              <Card key={b.id}>
                <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="font-medium text-ink">{b.name}</p>
                    <p className="text-sm text-ink-muted">
                      {b.industry} · {b.email} · {b.member_count} üye
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={b.status}
                      onChange={(e) => handleStatusChange(b, e.target.value as AdminBusiness["status"])}
                      className="h-9 w-36"
                    >
                      <option value="ACTIVE">Aktif</option>
                      <option value="INACTIVE">Pasif</option>
                      <option value="SUSPENDED">Askıya alındı</option>
                    </Select>
                    <Select
                      value={b.plan}
                      onChange={(e) => handlePlanChange(b, e.target.value as AdminBusiness["plan"])}
                      className="h-9 w-32"
                    >
                      <option value="FREE">Free</option>
                      <option value="PRO">Pro</option>
                      <option value="ENTERPRISE">Enterprise</option>
                    </Select>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(b)}>
                      <Trash2 className="h-4 w-4 text-danger" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}