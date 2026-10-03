"use client";

import { useEffect, useState } from "react";
import { Plus, Banknote, Clock, CheckCircle2, TrendingUp, TrendingDown, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getTodayRegister,
  openCashRegister,
  closeCashRegister,
  addCashTransaction,
  getRegisterSummary,
  listCashRegisters,
  ApiError,
  CashRegister,
  CashTransaction,
  RegisterSummary,
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useConfirm } from "@/components/providers/confirm-dialog-provider";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string | null, includeTime = false) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return includeTime ? d.toLocaleString("tr-TR") : d.toLocaleDateString("tr-TR");
}

export default function CashRegisterPage() {
  const confirmDialog = useConfirm();
  const businessId = getActiveBusinessId();

  const [register, setRegister] = useState<CashRegister | null>(null);
  const [summary, setSummary] = useState<RegisterSummary | null>(null);
  const [pastRegisters, setPastRegisters] = useState<CashRegister[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Forms
  const [showOpenForm, setShowOpenForm] = useState(false);
  const [openBalance, setOpenBalance] = useState(0);

  const [showCloseForm, setShowCloseForm] = useState(false);
  const [closeBalance, setCloseBalance] = useState(0);
  const [closeNotes, setCloseNotes] = useState("");

  const [showTxForm, setShowTxForm] = useState(false);
  const [txForm, setTxForm] = useState({
    transaction_type: "DEPOSIT",
    amount: 0,
    description: "",
  });

  const refresh = async () => {
    if (!businessId) return;
    setLoading(true);
    setError(null);
    
    try {
      // Get today's register (404 = no register today, that's OK)
      const todayReg = await getTodayRegister(businessId).catch(e => {
        if (e instanceof ApiError && (e.status === 404 || e.status === 422)) return null;
        throw e;
      });
      setRegister(todayReg);

      if (todayReg && todayReg.status === 'OPEN') {
        const sum = await getRegisterSummary(businessId, todayReg.id).catch(() => null);
        setSummary(sum);
      } else {
        setSummary(null);
      }

      const history = await listCashRegisters(businessId, { page: 1 }).catch(() => []);
      setPastRegisters(history.filter((h: any) => h.id !== todayReg?.id).slice(0, 5));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kasa verileri yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    refresh();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId]);

  const handleOpen = async () => {
    if (!businessId) return;
    try {
      await openCashRegister(businessId, { opening_balance: openBalance });
      toast.success("Kasa açıldı.");
      setShowOpenForm(false);
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Kasa açılamadı.");
    }
  };

  const handleClose = async () => {
    if (!businessId || !register) return;
    try {
      await closeCashRegister(businessId, register.id, { closing_balance: closeBalance, notes: closeNotes });
      toast.success("Kasa kapatıldı.");
      setShowCloseForm(false);
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Kasa kapatılamadı.");
    }
  };

  const handleAddTx = async () => {
    if (!businessId || !register) return;
    if (txForm.amount <= 0 || !txForm.description.trim()) {
      toast.error("Geçerli bir tutar ve açıklama giriniz.");
      return;
    }
    try {
      await addCashTransaction(businessId, register.id, {
        transaction_type: txForm.transaction_type,
        amount: txForm.amount,
        description: txForm.description
      });
      toast.success("İşlem eklendi.");
      setShowTxForm(false);
      setTxForm({ transaction_type: "DEPOSIT", amount: 0, description: "" });
      refresh();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "İşlem eklenemedi.");
    }
  };

  if (error) {
    return <div className="flex items-center justify-center h-64 text-danger">{error}</div>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Kasa Takibi</h1>
          <p className="mt-1 text-sm text-ink-muted">Günlük kasa açılış/kapanış ve nakit akışını yönetin.</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-8 text-ink-muted"><Clock className="animate-spin w-5 h-5 mr-2" /> Yükleniyor...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content (Status & summary) */}
          <div className="col-span-1 lg:col-span-2 space-y-6">
            
            {/* Today's Status */}
            <Card className="bg-surface-elevated border-border overflow-hidden">
              <div className={cn("h-2 w-full", register?.status === 'OPEN' ? "bg-emerald-500" : register?.status === 'CLOSED' ? "bg-zinc-500" : "bg-blue-500")}></div>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-surface rounded-full">
                      <Store className="w-8 h-8 text-ink-muted" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-ink">Bugünün Kasası</h2>
                      <p className="text-sm text-ink-muted">{formatDate(new Date().toISOString())}</p>
                    </div>
                  </div>
                  <div>
                    {register ? (
                      <span className={cn(
                        "px-3 py-1 text-sm font-medium rounded-full",
                        register.status === 'OPEN' ? "bg-emerald-500/15 text-emerald-400" : "bg-zinc-500/15 text-zinc-400"
                      )}>
                        {register.status === 'OPEN' ? 'Açık' : 'Kapalı'}
                      </span>
                    ) : (
                      <span className="px-3 py-1 text-sm font-medium rounded-full bg-blue-500/15 text-blue-400">Henüz Açılmadı</span>
                    )}
                  </div>
                </div>

                {(!register || register.status === 'CLOSED') && (
                  <div className="mt-6 pt-6 border-t border-border">
                    {showOpenForm ? (
                      <div className="flex gap-4 items-end">
                        <div className="flex-1 space-y-2">
                          <Label>Açılış Bakiyesi (₺)</Label>
                          <Input type="number" min={0} step={0.01} value={openBalance} onChange={e => setOpenBalance(parseFloat(e.target.value) || 0)} />
                        </div>
                        <Button onClick={handleOpen} className="bg-emerald-600 hover:bg-emerald-700">Kasayı Aç</Button>
                        <Button variant="outline" onClick={() => setShowOpenForm(false)}>İptal</Button>
                      </div>
                    ) : (
                      <Button onClick={() => setShowOpenForm(true)} className="w-full bg-emerald-600 hover:bg-emerald-700 h-12">
                        Yeni Kasa Aç
                      </Button>
                    )}
                  </div>
                )}

                {register && (
                  <div className="mt-6 grid grid-cols-2 gap-4">
                    <div className="bg-surface p-4 rounded-lg">
                      <p className="text-xs text-ink-muted mb-1">Açılış Bakiyesi</p>
                      <p className="text-lg font-bold text-ink">{formatCurrency(register.opening_balance)}</p>
                    </div>
                    <div className="bg-surface p-4 rounded-lg">
                      <p className="text-xs text-ink-muted mb-1">{register.status === 'CLOSED' ? 'Kapanış Bakiyesi' : 'Mevcut Bakiye (Beklenen)'}</p>
                      <p className="text-lg font-bold text-blue-400">{formatCurrency(summary?.expected_closing || register.closing_balance || 0)}</p>
                    </div>
                  </div>
                )}

                {register && register.status === 'OPEN' && (
                  <div className="mt-6 pt-6 border-t border-border">
                    <Button onClick={() => { setCloseBalance(summary?.expected_closing || 0); setShowCloseForm(true); }} variant="outline" className="w-full border-red-500/50 text-red-400 hover:bg-red-500/10">
                      Kasayı Kapat
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Close Register Modal */}
            {showCloseForm && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                <Card className="w-full max-w-md bg-surface-elevated border-border shadow-xl">
                  <CardHeader>
                    <CardTitle>Kasa Kapatma</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between text-sm p-3 bg-surface rounded">
                      <span className="text-ink-muted">Sistemdeki Bakiye:</span>
                      <span className="font-bold">{formatCurrency(summary?.expected_closing || 0)}</span>
                    </div>
                    <div className="space-y-2">
                      <Label>Sayım Sonucu Gerçek Bakiye (₺) *</Label>
                      <Input type="number" min={0} step={0.01} value={closeBalance} onChange={e => setCloseBalance(parseFloat(e.target.value) || 0)} />
                    </div>
                    {(closeBalance - (summary?.expected_closing || 0)) !== 0 && (
                      <div className={cn("text-sm p-2 rounded", (closeBalance - (summary?.expected_closing || 0)) > 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400")}>
                        Fark: {formatCurrency(closeBalance - (summary?.expected_closing || 0))}
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label>Notlar (İsteğe bağlı)</Label>
                      <Input value={closeNotes} onChange={e => setCloseNotes(e.target.value)} placeholder="Örn: Bozuk para eksiği" />
                    </div>
                    <div className="flex gap-2 justify-end pt-2">
                      <Button variant="outline" onClick={() => setShowCloseForm(false)}>İptal</Button>
                      <Button onClick={handleClose} className="bg-red-600 hover:bg-red-700">Kapat</Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

          </div>

          {/* Sidebar Area */}
          <div className="col-span-1 space-y-6">
            
            {register && register.status === 'OPEN' && (
              <Card className="bg-surface-elevated border-border">
                <CardHeader className="pb-3 border-b border-border">
                  <CardTitle className="text-sm font-semibold flex justify-between items-center">
                    İşlem Ekle
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setShowTxForm(!showTxForm)}><Plus className="h-4 w-4" /></Button>
                  </CardTitle>
                </CardHeader>
                {showTxForm && (
                  <CardContent className="pt-4 space-y-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Tür</Label>
                      <select className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm" value={txForm.transaction_type} onChange={e => setTxForm({...txForm, transaction_type: e.target.value})}>
                        <option value="SALE">Satış Geliri</option>
                        <option value="DEPOSIT">Para Girişi</option>
                        <option value="WITHDRAWAL">Para Çıkışı</option>
                        <option value="EXPENSE">Masraf/Gider</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Tutar (₺)</Label>
                      <Input type="number" min={0} step={0.01} value={txForm.amount || ''} onChange={e => setTxForm({...txForm, amount: parseFloat(e.target.value) || 0})} className="h-8 text-sm" />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Açıklama</Label>
                      <Input value={txForm.description} onChange={e => setTxForm({...txForm, description: e.target.value})} className="h-8 text-sm" placeholder="Açıklama..." />
                    </div>
                    <Button onClick={handleAddTx} className="w-full h-8 text-xs">Kaydet</Button>
                  </CardContent>
                )}
              </Card>
            )}

            {summary && (
              <Card className="bg-surface-elevated border-border">
                <CardHeader className="pb-3 border-b border-border">
                  <CardTitle className="text-sm font-semibold">Özet Tablo</CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-2 text-sm">
                  <div className="flex justify-between text-ink-muted"><span>Satışlar</span><span className="text-emerald-400">+{formatCurrency(summary.total_sales)}</span></div>
                  <div className="flex justify-between text-ink-muted"><span>Nakit Girişleri</span><span className="text-emerald-400">+{formatCurrency(summary.total_deposits)}</span></div>
                  <div className="flex justify-between text-ink-muted"><span>Giderler</span><span className="text-red-400">-{formatCurrency(summary.total_expenses)}</span></div>
                  <div className="flex justify-between text-ink-muted"><span>Nakit Çıkışları</span><span className="text-red-400">-{formatCurrency(summary.total_withdrawals)}</span></div>
                </CardContent>
              </Card>
            )}

            {pastRegisters.length > 0 && (
              <Card className="bg-surface-elevated border-border">
                <CardHeader className="pb-3 border-b border-border">
                  <CardTitle className="text-sm font-semibold">Son Kasalar</CardTitle>
                </CardHeader>
                <CardContent className="pt-0 px-0">
                  <div className="divide-y divide-border">
                    {pastRegisters.map(r => (
                      <div key={r.id} className="p-4 text-sm flex justify-between items-center hover:bg-white/[0.02]">
                        <div>
                          <p className="font-medium">{formatDate(r.register_date)}</p>
                          <p className="text-xs text-ink-muted">Fark: <span className={cn(r.difference && r.difference > 0 ? "text-emerald-400" : r.difference && r.difference < 0 ? "text-red-400" : "text-ink")}>{formatCurrency(r.difference || 0)}</span></p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold">{formatCurrency(r.closing_balance || 0)}</p>
                          <p className="text-[10px] text-ink-muted uppercase">{r.status}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
