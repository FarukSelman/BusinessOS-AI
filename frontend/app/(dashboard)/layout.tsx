import { Sidebar } from "@/components/layout/sidebar";
import { Navbar } from "@/components/layout/navbar";
import { AuthGuard } from "@/components/layout/auth-guard";
import { ConfirmDialogProvider } from "@/components/providers/confirm-dialog-provider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <ConfirmDialogProvider>
        <div className="flex">
          <Sidebar />
          <div className="flex flex-1 flex-col">
            <Navbar />
            <main className="flex-1 bg-surface p-6">{children}</main>
          </div>
        </div>
      </ConfirmDialogProvider>
    </AuthGuard>
  );
}