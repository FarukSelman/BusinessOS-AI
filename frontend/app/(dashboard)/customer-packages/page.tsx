"use client";

import { useEffect, useState } from "react";
import { Users, CheckCircle2, Clock, Plus, Search, Calendar, CreditCard, Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import {
  listCustomerPackages,
  sellPackage,
  listCustomers,
  listPackages,
  getCustomerPackageDetail,
  completeSession,
  cancelSession,
  payInstallment,
  ApiError,
  CustomerPackage,
  Customer,
  ServicePackage
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return "Süresiz";
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

export default function CustomerPackagesPage() {
  const businessId = getActiveBusinessId();

  const [cPackages, setCPackages] = useState<CustomerPackage[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [packages, setPackages] = useState<ServicePackage[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  const [showSell, setShowSell] = useState(false);
  const [selling, setSelling] = useState(false);
  const [sellForm, setSellForm] = useState({
    customer_id: "",
    package_id: "",
    installments: 1,
    payment_method: "CREDIT_CARD",
    notes: ""
  });

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedCp, setSelectedCp] = useState<CustomerPackage | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"SESSIONS" | "INSTALLMENTS">("SESSIONS");

  const selectedPkg = packages.find(p => p.id === sellForm.package_id);

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      const [cps, custs, pkgs] = await Promise.all([
        listCustomerPackages(businessId, { status: statusFilter || undefined }),
        listCustomers(businessId, 1, 1000),
        listPackages(businessId)
      ]);
      setCPackages(cps);
      setCustomers(custs);
      setPackages(pkgs);
    } catch (err) {
      toast.error("Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [businessId, statusFilter]);

  const handleSell = async () => {
    if (!businessId) return;
    if (!sellForm.customer_id || !sellForm.package_id) {
      toast.error("Müşteri ve paket seçilmelidir.");
      return;
    }
    setSelling(true);
    try {
      await sellPackage(businessId, {
        customer_id: sellForm.customer_id,
        package_id: sellForm.package_id,
        installment_count: sellForm.installments,
        payment_method: sellForm.payment_method,
        notes: sellForm.notes || null
      });
      toast.success("Paket satışı tamamlandı.");
      setShowSell(false);
      setSellForm({ customer_id: "", package_id: "", installments: 1, payment_method: "CREDIT_CARD", notes: "" });
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Satış başarısız.");
    } finally {
      setSelling(false);
    }
  };

  const openDetail = async (cpId: string) => {
    if (!businessId) return;
    setDetailOpen(true);
    setDetailLoading(true);
    setSelectedCp(null);
    setActiveTab("SESSIONS");
    try {
      const detail = await getCustomerPackageDetail(businessId, cpId);
      setSelectedCp(detail);
    } catch (err) {
      toast.error("Detay yüklenemedi.");
      setDetailOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCompleteSession = async (sessionId: string) => {
    if (!businessId || !selectedCp) return;
    try {
      await completeSession(businessId, selectedCp.id, sessionId, { notes: "Manuel tamamlandı" });
      toast.success("Seans tamamlandı.");
      openDetail(selectedCp.id);
      refresh();
    } catch (err) {
      toast.error("İşlem başarısız.");
    }
  };

  const handleCancelSession = async (sessionId: string) => {
    if (!businessId || !selectedCp) return;
    try {
      await cancelSession(businessId, selectedCp.id, sessionId);
      toast.success("Seans iptal edildi.");
      openDetail(selectedCp.id);
      refresh();
    } catch (err) {
      toast.error("İşlem başarısız.");
    }
  };

  const handlePayInstallment = async (instId: string) => {
    if (!businessId || !selectedCp) return;
    try {
      await payInstallment(businessId, instId, { payment_method: "CREDIT_CARD" });
      toast.success("Taksit ödendi.");
      openDetail(selectedCp.id);
      refresh();
    } catch (err) {
      toast.error("İşlem başarısız.");
    }
  };

  const filteredCPackages = cPackages.filter(cp => 
    !search || cp.customer_name?.toLowerCase().includes(search.toLowerCase()) || cp.package_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Müşteri Paketleri</h1>
          <p className="mt-1 text-sm text-ink-muted">Satılan paketlerin seans ve ödeme takibi.</p>
        </div>
        <Button onClick={() => setShowSell(!showSell)} className="gap-2" style={{ backgroundColor: "var(--agent-appointments)" }}>
          <Plus className="h-4 w-4" />
          {showSell ? "İptal" : "Paket Sat"}
        </Button>
      </div>

      {showSell && (
        <Card className="bg-surface-elevated border-border">
          <CardHeader>
            <CardTitle className="text-lg">Yeni Paket Satışı</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Müşteri *</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={sellForm.customer_id}
                  onChange={e => setSellForm({...sellForm, customer_id: e.target.value})}
                >
                  <option value="">Seçiniz...</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Paket *</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={sellForm.package_id}
                  onChange={e => {
                    setSellForm({...sellForm, package_id: e.target.value, installments: 1});
                  }}
                >
                  <option value="">Seçiniz...</option>
                  {packages.map(p => <option key={p.id} value={p.id}>{p.name} ({formatCurrency(p.price)})</option>)}
                </select>
              </div>
              
              {selectedPkg && (
                <div className="space-y-1">
                  <Label>Taksit Sayısı (1 = Peşin)</Label>
                  <Input 
                    type="number" min="1" max={selectedPkg.is_installment_allowed ? selectedPkg.max_installments : 1}
                    value={sellForm.installments} 
                    onChange={e => setSellForm({...sellForm, installments: parseInt(e.target.value) || 1})} 
                    disabled={!selectedPkg.is_installment_allowed}
                  />
                  {!selectedPkg.is_installment_allowed && <p className="text-xs text-ink-muted">Bu pakette taksit imkanı yoktur.</p>}
                  {selectedPkg.is_installment_allowed && <p className="text-xs text-ink-muted">Maks: {selectedPkg.max_installments} taksit</p>}
                </div>
              )}

              <div className="space-y-1">
                <Label>Peşinat/İlk Ödeme Yöntemi</Label>
                <select 
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
                  value={sellForm.payment_method}
                  onChange={e => setSellForm({...sellForm, payment_method: e.target.value})}
                >
                  <option value="CASH">Nakit</option>
                  <option value="CREDIT_CARD">Kredi Kartı</option>
                  <option value="BANK_TRANSFER">Havale/EFT</option>
                </select>
              </div>

              <div className="space-y-1 md:col-span-2">
                <Label>Notlar</Label>
                <Input value={sellForm.notes} onChange={e => setSellForm({...sellForm, notes: e.target.value})} />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSell} disabled={selling} style={{ backgroundColor: "var(--agent-appointments)" }}>
                {selling ? "İşleniyor..." : "Satışı Onayla"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col md:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-muted" />
          <Input 
            className="pl-9 w-full" 
            placeholder="Müşteri veya Paket Ara..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select 
          className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent w-full md:w-auto"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="">Tüm Durumlar</option>
          <option value="ACTIVE">Aktif</option>
          <option value="COMPLETED">Tamamlanan</option>
          <option value="EXPIRED">Süresi Dolan</option>
          <option value="CANCELLED">İptal Edilen</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-8 text-ink-muted">Yükleniyor...</div>
      ) : filteredCPackages.length === 0 ? (
        <Card className="bg-surface-elevated border-border text-center py-12 text-ink-muted">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p>Kayıt bulunamadı.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCPackages.map(cp => {
            const progress = cp.total_sessions > 0 ? (cp.used_sessions / cp.total_sessions) * 100 : 0;
            return (
              <Card key={cp.id} className="bg-surface-elevated border-border hover:border-accent transition-colors cursor-pointer" onClick={() => openDetail(cp.id)}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base text-ink">{cp.customer_name}</CardTitle>
                      <p className="text-sm font-medium text-accent mt-0.5">{cp.package_name}</p>
                    </div>
                    <span className={cn(
                      "px-2 py-0.5 text-[10px] rounded-full uppercase font-bold tracking-wider",
                      cp.status === 'ACTIVE' ? "bg-emerald-500/15 text-emerald-400" :
                      cp.status === 'COMPLETED' ? "bg-blue-500/15 text-blue-400" :
                      cp.status === 'CANCELLED' ? "bg-red-500/15 text-red-400" :
                      "bg-zinc-500/15 text-zinc-400"
                    )}>
                      {cp.status === 'ACTIVE' ? 'Aktif' : cp.status === 'COMPLETED' ? 'Bitti' : cp.status === 'EXPIRED' ? 'Süresi Doldu' : 'İptal'}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-ink-muted">
                      <span>Kullanılan Seans</span>
                      <span className="font-medium text-ink">{cp.used_sessions} / {cp.total_sessions}</span>
                    </div>
                    <div className="h-2 w-full bg-black/20 rounded-full overflow-hidden">
                      <div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1 text-sm border-t border-white/5 pt-3">
                    <div className="flex justify-between">
                      <span className="text-ink-muted">Ödenen Tutar:</span>
                      <span className="text-ink font-medium">{formatCurrency(cp.paid_amount)} / {formatCurrency(cp.total_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-ink-muted">Son Kullanma:</span>
                      <span className="text-ink font-medium">{formatDate(cp.expires_at)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          {detailLoading || !selectedCp ? (
            <div className="flex items-center justify-center p-8"><Clock className="w-6 h-6 animate-spin text-ink-muted" /></div>
          ) : (
            <div className="space-y-6">
              <div>
                <DialogTitle className="text-xl mb-1">{selectedCp.customer_name}</DialogTitle>
                <DialogDescription className="text-base text-accent font-medium">{selectedCp.package_name}</DialogDescription>
              </div>

              <div className="flex gap-4 border-b border-border">
                <button 
                  className={cn("pb-2 px-1 text-sm font-medium border-b-2 transition-colors", activeTab === "SESSIONS" ? "border-accent text-accent" : "border-transparent text-ink-muted hover:text-ink")}
                  onClick={() => setActiveTab("SESSIONS")}
                >
                  Seanslar ({selectedCp.used_sessions}/{selectedCp.total_sessions})
                </button>
                <button 
                  className={cn("pb-2 px-1 text-sm font-medium border-b-2 transition-colors", activeTab === "INSTALLMENTS" ? "border-accent text-accent" : "border-transparent text-ink-muted hover:text-ink")}
                  onClick={() => setActiveTab("INSTALLMENTS")}
                >
                  Taksitler ({selectedCp.installments?.filter(i => i.status === 'PAID').length || 0}/{selectedCp.installments?.length || 0})
                </button>
              </div>

              {activeTab === "SESSIONS" && (
                <div className="space-y-3">
                  {selectedCp.sessions?.map(session => (
                    <div key={session.id} className="flex items-center justify-between p-3 rounded-md border border-border bg-surface hover:bg-surface-elevated transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center text-xs font-bold">
                          {session.session_number}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-ink flex items-center gap-2">
                            Seans {session.session_number}
                            <span className={cn(
                              "px-1.5 py-0.5 text-[10px] rounded uppercase font-bold tracking-wider",
                              session.status === 'COMPLETED' ? "bg-emerald-500/15 text-emerald-400" :
                              session.status === 'PENDING' ? "bg-yellow-500/15 text-yellow-400" :
                              session.status === 'CANCELLED' ? "bg-zinc-500/15 text-zinc-400" :
                              "bg-red-500/15 text-red-400"
                            )}>
                              {session.status}
                            </span>
                          </div>
                          {session.session_date && <div className="text-xs text-ink-muted flex items-center mt-1"><Calendar className="w-3 h-3 mr-1" /> {formatDate(session.session_date)}</div>}
                        </div>
                      </div>
                      
                      {session.status === 'PENDING' && selectedCp.status === 'ACTIVE' && (
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" className="h-8 text-danger border-danger/30 hover:bg-danger/10" onClick={() => handleCancelSession(session.id)}>İptal</Button>
                          <Button size="sm" className="h-8 bg-emerald-600 hover:bg-emerald-700" onClick={() => handleCompleteSession(session.id)}>Tamamla</Button>
                        </div>
                      )}
                    </div>
                  ))}
                  {(!selectedCp.sessions || selectedCp.sessions.length === 0) && (
                    <div className="text-center py-4 text-ink-muted">Seans kaydı yok.</div>
                  )}
                </div>
              )}

              {activeTab === "INSTALLMENTS" && (
                <div className="space-y-3">
                  {selectedCp.installments?.map(inst => (
                    <div key={inst.id} className={cn(
                      "flex items-center justify-between p-3 rounded-md border border-border bg-surface hover:bg-surface-elevated transition-colors",
                      inst.status === "OVERDUE" && "border-l-2 border-l-red-500"
                    )}>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center text-xs font-bold">
                          {inst.installment_number}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-ink flex items-center gap-2">
                            {formatCurrency(inst.amount)}
                            <span className={cn(
                              "px-1.5 py-0.5 text-[10px] rounded uppercase font-bold tracking-wider",
                              inst.status === 'PAID' ? "bg-emerald-500/15 text-emerald-400" :
                              inst.status === 'PENDING' ? "bg-yellow-500/15 text-yellow-400" :
                              inst.status === 'OVERDUE' ? "bg-red-500/15 text-red-400" :
                              "bg-zinc-500/15 text-zinc-400"
                            )}>
                              {inst.status === 'OVERDUE' ? 'Gecikmiş' : inst.status === 'PAID' ? 'Ödendi' : inst.status === 'PENDING' ? 'Bekliyor' : 'İptal'}
                            </span>
                          </div>
                          <div className="text-xs text-ink-muted flex items-center mt-1">
                            <Clock className="w-3 h-3 mr-1" /> Vade: {formatDate(inst.due_date)}
                            {inst.paid_date && <span className="ml-2 text-emerald-400/80">Ödendi: {formatDate(inst.paid_date)}</span>}
                          </div>
                        </div>
                      </div>
                      
                      {(inst.status === 'PENDING' || inst.status === 'OVERDUE') && (
                        <Button size="sm" onClick={() => handlePayInstallment(inst.id)} style={{ backgroundColor: "var(--agent-finance)" }}>
                          Öde
                        </Button>
                      )}
                    </div>
                  ))}
                  {(!selectedCp.installments || selectedCp.installments.length === 0) && (
                    <div className="text-center py-4 text-ink-muted">Taksit kaydı yok.</div>
                  )}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
