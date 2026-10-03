"use client";

import { useEffect, useState } from "react";
import { User, Mail, Shield, CheckCircle2, Lock, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getMe, updateProfile, changePassword, MeResponse, ApiError } from "@/lib/api";
import { toast } from "sonner";

export default function ProfilePage() {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    getMe()
      .then((data) => {
        setUser(data);
        setFirstName(data.first_name);
        setLastName(data.last_name);
      })
      .catch((err) => {
        toast.error("Profil bilgileri alınamadı.");
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) {
      toast.error("Ad ve soyad boş bırakılamaz.");
      return;
    }

    setSavingProfile(true);
    try {
      const updated = await updateProfile({
        first_name: firstName,
        last_name: lastName,
      });
      setUser(updated);
      toast.success("Profil başarıyla güncellendi.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Profil güncellenemedi.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Tüm alanları doldurmalısın.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Yeni şifreler eşleşmiyor.");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Yeni şifre en az 8 karakter olmalıdır.");
      return;
    }

    setSavingPassword(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success("Şifren başarıyla güncellendi.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Şifre değiştirilemedi.");
    } finally {
      setSavingPassword(false);
    }
  }

  if (loading) {
    return <div className="p-6 text-sm text-ink-muted">Yükleniyor...</div>;
  }

  if (!user) {
    return <div className="p-6 text-sm text-danger">Profil bilgileri bulunamadı.</div>;
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      <div className="border-l-2 pl-3 border-accent">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">
          Profilim
        </h1>
        <p className="text-sm text-ink-muted">
          Kişisel bilgilerini ve hesap güvenliğini yönet.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-6">
          <Card>
            <CardContent className="p-6 flex flex-col items-center text-center">
              <div className="h-20 w-20 rounded-full bg-accent/10 flex items-center justify-center text-accent mb-4">
                <User className="h-10 w-10" />
              </div>
              <h2 className="text-xl font-semibold text-ink">{user.first_name} {user.last_name}</h2>
              <p className="text-sm text-ink-muted flex items-center gap-2 mt-1">
                <Mail className="h-4 w-4" />
                {user.email}
              </p>
              
              <div className="mt-4 flex flex-col gap-2 w-full">
                <div className="flex items-center justify-between text-sm px-3 py-2 bg-surface-elevated rounded-md border border-border">
                  <span className="text-ink-muted flex items-center gap-2">
                    <Shield className="h-4 w-4" /> Rol
                  </span>
                  <span className="font-medium text-ink">
                    {user.is_superadmin ? "Superadmin" : "Kullanıcı"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm px-3 py-2 bg-surface-elevated rounded-md border border-border">
                  <span className="text-ink-muted flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Durum
                  </span>
                  <span className="font-medium text-ink capitalize">
                    {user.status.toLowerCase()}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Kişisel Bilgiler</CardTitle>
              <CardDescription>Adını ve soyadını güncelle.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">Ad</Label>
                    <Input 
                      id="firstName" 
                      value={firstName} 
                      onChange={(e) => setFirstName(e.target.value)} 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Soyad</Label>
                    <Input 
                      id="lastName" 
                      value={lastName} 
                      onChange={(e) => setLastName(e.target.value)} 
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={savingProfile} className="gap-2">
                    <Save className="h-4 w-4" />
                    {savingProfile ? "Kaydediliyor..." : "Kaydet"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Şifre Değiştir</CardTitle>
              <CardDescription>Hesap güvenliğin için güçlü bir şifre kullan.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleChangePassword} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Mevcut Şifre</Label>
                  <Input 
                    id="currentPassword" 
                    type="password"
                    value={currentPassword} 
                    onChange={(e) => setCurrentPassword(e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="newPassword">Yeni Şifre</Label>
                  <Input 
                    id="newPassword" 
                    type="password"
                    value={newPassword} 
                    onChange={(e) => setNewPassword(e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Yeni Şifre (Tekrar)</Label>
                  <Input 
                    id="confirmPassword" 
                    type="password"
                    value={confirmPassword} 
                    onChange={(e) => setConfirmPassword(e.target.value)} 
                  />
                </div>
                <div className="flex justify-end">
                  <Button type="submit" variant="outline" disabled={savingPassword} className="gap-2">
                    <Lock className="h-4 w-4" />
                    {savingPassword ? "Güncelleniyor..." : "Şifreyi Güncelle"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
