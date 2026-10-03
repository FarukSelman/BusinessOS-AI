"use client";

import { useEffect, useState } from "react";
import { UserPlus, Trash2, Mail, Clock, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getMe,
  listMemberships,
  updateMembershipRole,
  removeMembership,
  listInvitations,
  createInvitation,
  type Membership,
  type MembershipRole,
  type Invitation,
  ApiError,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const roleLabels: Record<MembershipRole, string> = {
  OWNER: "Sahip",
  ADMIN: "Yönetici",
  EMPLOYEE: "Çalışan",
  VIEWER: "İzleyici",
};

const invitationStatusLabels: Record<string, { label: string; color: string }> = {
  PENDING: { label: "Bekliyor", color: "var(--agent-appointments)" },
  ACCEPTED: { label: "Kabul edildi", color: "var(--agent-sales)" },
  DECLINED: { label: "Reddedildi", color: "var(--danger)" },
  CANCELLED: { label: "İptal edildi", color: "var(--ink-muted)" },
  EXPIRED: { label: "Süresi doldu", color: "var(--ink-muted)" },
};

const assignableRoles: MembershipRole[] = ["ADMIN", "EMPLOYEE", "VIEWER"];

export default function TeamPage() {
  const businessId = getActiveBusinessId();

  const [myUserId, setMyUserId] = useState<string | null>(null);
  const [members, setMembers] = useState<Membership[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<MembershipRole>("EMPLOYEE");
  const [inviting, setInviting] = useState(false);

  const myMembership = members.find((m) => m.user.id === myUserId);
  const myRole = myMembership?.role;
  const canManage = myRole === "OWNER" || myRole === "ADMIN"; // rol değiştirme/davet
  const canRemove = myRole === "OWNER"; // üye çıkarma

  useEffect(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }

    Promise.all([getMe(), listMemberships(businessId)])
      .then(async ([me, memberList]) => {
        setMyUserId(me.id);
        setMembers(memberList);

        const myEntry = memberList.find((m) => m.user.id === me.id);
        if (myEntry?.role === "OWNER") {
          try {
            const invites = await listInvitations(businessId);
            setInvitations(invites);
          } catch {
            // davet listesi görülemiyorsa sessizce geç
          }
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Ekip bilgileri yüklenemedi."))
      .finally(() => setLoading(false));
  }, [businessId]);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!businessId || !inviteEmail.trim()) return;
    setInviting(true);
    setError(null);
    try {
      const invitation = await createInvitation(businessId, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInvitations((prev) => [invitation, ...prev]);
      setInviteEmail("");
      setInviteRole("EMPLOYEE");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Davet gönderilemedi.");
    } finally {
      setInviting(false);
    }
  }

  async function handleRoleChange(membershipId: string, role: MembershipRole) {
    if (!businessId) return;
    try {
      const updated = await updateMembershipRole(businessId, membershipId, role);
      setMembers((prev) => prev.map((m) => (m.id === membershipId ? updated : m)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rol güncellenemedi.");
    }
  }

  async function handleRemove(membershipId: string) {
    if (!businessId) return;
    if (!confirm("Bu kişiyi işletmeden çıkarmak istediğine emin misin?")) return;
    try {
      await removeMembership(businessId, membershipId);
      setMembers((prev) => prev.filter((m) => m.id !== membershipId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Çıkarılamadı.");
    }
  }

  async function handleCopyLink(token: string) {
    const link = `${window.location.origin}/invitations/accept/${token}`;
    try {
      await navigator.clipboard.writeText(link);
      toast.success("Davet linki kopyalandı.");
    } catch {
      toast.error("Kopyalanamadı, linki elle seçip kopyalayabilirsin.");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Ekip</h1>
        <p className="text-sm text-ink-muted">İşletmendeki kişileri ve rollerini yönet.</p>
      </div>

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>}

      {loading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : (
        <>
          {canManage && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Davet gönder</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleInvite} className="flex flex-col gap-4 sm:flex-row sm:items-end">
                  <div className="flex flex-1 flex-col gap-1.5">
                    <Label htmlFor="invite-email">E-posta</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      placeholder="ornek@sirket.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5 sm:w-48">
                    <Label htmlFor="invite-role">Rol</Label>
                    <Select
                      id="invite-role"
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value as MembershipRole)}
                    >
                      {assignableRoles.map((r) => (
                        <option key={r} value={r}>
                          {roleLabels[r]}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <Button type="submit" disabled={inviting} className="gap-2 sm:w-auto">
                    <UserPlus className="h-4 w-4" />
                    {inviting ? "Gönderiliyor..." : "Davet gönder"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-ink-muted">Üyeler ({members.length})</h2>
            {members.map((m) => (
              <Card key={m.id}>
                <CardContent className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="font-medium text-ink">
                      {m.user.first_name} {m.user.last_name}
                      {m.user.id === myUserId && (
                        <span className="ml-2 text-xs font-normal text-ink-muted">(sen)</span>
                      )}
                    </p>
                    <p className="text-sm text-ink-muted">{m.user.email}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {canManage && m.role !== "OWNER" ? (
                      <Select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.id, e.target.value as MembershipRole)}
                        className="h-9 w-36"
                      >
                        {assignableRoles.map((r) => (
                          <option key={r} value={r}>
                            {roleLabels[r]}
                          </option>
                        ))}
                      </Select>
                    ) : (
                      <span
                        className={cn(
                          "rounded-full px-2.5 py-1 text-xs font-medium",
                          m.role === "OWNER"
                            ? "bg-[color-mix(in_srgb,var(--accent)_15%,transparent)] text-accent"
                            : "bg-surface text-ink-muted"
                        )}
                      >
                        {roleLabels[m.role]}
                      </span>
                    )}
                    {canRemove && m.role !== "OWNER" && (
                      <Button variant="ghost" size="icon" onClick={() => handleRemove(m.id)}>
                        <Trash2 className="h-4 w-4 text-danger" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {myRole === "OWNER" && (
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold text-ink-muted">Bekleyen davetler</h2>
              {invitations.length === 0 ? (
                <p className="text-sm text-ink-muted">Bekleyen davet yok.</p>
              ) : (
                invitations.map((inv) => {
                  const style = invitationStatusLabels[inv.status];
                  return (
                    <Card key={inv.id}>
                      <CardContent className="flex items-center justify-between gap-4 p-4">
                        <div className="flex items-center gap-2 text-sm">
                          <Mail className="h-4 w-4 text-ink-muted" />
                          <span className="font-medium text-ink">{inv.email}</span>
                          <span className="text-ink-muted">· {roleLabels[inv.role]}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {inv.status === "PENDING" && (
                            <span className="flex items-center gap-1 text-xs text-ink-muted">
                              <Clock className="h-3 w-3" />
                              {new Date(inv.expires_at).toLocaleDateString("tr-TR")} tarihine kadar geçerli
                            </span>
                          )}
                          <span
                            className="rounded-full px-2.5 py-1 text-xs font-medium"
                            style={{
                              backgroundColor: `color-mix(in srgb, ${style.color} 15%, transparent)`,
                              color: style.color,
                            }}
                          >
                            {style.label}
                          </span>
                          {inv.status === "PENDING" && (
                            <Button variant="ghost" size="icon" onClick={() => handleCopyLink(inv.token)}>
                              <Copy className="h-4 w-4 text-ink-muted" />
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
