"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, XCircle, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { acceptInvitation, ApiError, type Invitation } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { saveActiveBusinessId } from "@/lib/business";

const roleLabels: Record<string, string> = {
  OWNER: "Sahip",
  ADMIN: "Yönetici",
  EMPLOYEE: "Çalışan",
  VIEWER: "İzleyici",
};

export default function AcceptInvitationPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();

  const [status, setStatus] = useState<"checking" | "loading" | "success" | "error">("checking");
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      const currentPath = `/invitations/accept/${params.token}`;
      router.replace(`/login?redirect=${encodeURIComponent(currentPath)}`);
      return;
    }

    setStatus("loading");
    acceptInvitation(params.token)
      .then((inv) => {
        setInvitation(inv);
        setStatus("success");
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Davet kabul edilemedi.");
        setStatus("error");
      });
  }, [params.token, router]);

  function goToBusiness() {
    if (invitation) {
      saveActiveBusinessId(invitation.business.id);
    }
    router.push("/dashboard");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <Card className="w-full max-w-sm">
        {(status === "checking" || status === "loading") && (
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <p className="text-sm text-ink-muted">Davet kontrol ediliyor...</p>
          </CardContent>
        )}

        {status === "success" && invitation && (
          <>
            <CardHeader className="items-center text-center">
              <CheckCircle2 className="h-10 w-10" style={{ color: "var(--agent-sales)" }} />
              <CardTitle>Davete katıldın!</CardTitle>
              <CardDescription>
                <span className="flex items-center justify-center gap-1.5">
                  <Building2 className="h-4 w-4" />
                  {invitation.business.name}
                </span>
                işletmesine <span className="font-medium text-ink">{roleLabels[invitation.role]}</span> rolüyle
                katıldın.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" onClick={goToBusiness}>
                İşletmeye git
              </Button>
            </CardContent>
          </>
        )}

        {status === "error" && (
          <>
            <CardHeader className="items-center text-center">
              <XCircle className="h-10 w-10 text-danger" />
              <CardTitle>Davet kabul edilemedi</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full" onClick={() => router.push("/select-business")}>
                İşletmelerime git
              </Button>
            </CardContent>
          </>
        )}
      </Card>
    </div>
  );
}
