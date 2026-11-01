import { DashboardShell } from "@/components/layout/dashboard-shell";
import { AuthGuard } from "@/components/layout/auth-guard";
import { ConfirmDialogProvider } from "@/components/providers/confirm-dialog-provider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <ConfirmDialogProvider>
        <DashboardShell>{children}</DashboardShell>
      </ConfirmDialogProvider>
    </AuthGuard>
  );
}