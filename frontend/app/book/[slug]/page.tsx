"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Calendar, Clock, User, CheckCircle2, ChevronRight, ChevronLeft,
  Phone, Mail, Loader2, Sparkles, Star, Building2
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───
interface ServiceInfo {
  id: string; name: string; description: string | null; price: number; duration: number;
}
interface BusinessInfo {
  id: string; name: string; slug: string; industry: string | null;
  logo_url: string | null; description: string | null; services: ServiceInfo[];
}
interface BranchInfo { id: string; name: string; address: string | null; }
interface StaffInfo {
  id: string; full_name: string; title: string | null; avatar_url: string | null; color: string;
  services: { id: string; name: string }[];
}

// ─── Helpers ───
function formatCurrency(n: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(n);
}
function formatDate(d: string) {
  return new Date(d).toLocaleDateString("tr-TR", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
}

const STEPS = ["Hizmet", "Personel", "Tarih & Saat", "Bilgiler", "Onay"];

export default function PublicBookingPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [step, setStep] = useState(0);
  const [business, setBusiness] = useState<BusinessInfo | null>(null);
  const [branches, setBranches] = useState<BranchInfo[]>([]);
  const [staffList, setStaffList] = useState<StaffInfo[]>([]);
  const [slots, setSlots] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Selections
  const [selectedService, setSelectedService] = useState<ServiceInfo | null>(null);
  const [selectedStaff, setSelectedStaff] = useState<StaffInfo | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<BranchInfo | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [form, setForm] = useState({ name: "", phone: "", email: "" });

  // Load business info + branches
  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/v1/public/booking/${slug}/info`).then(r => r.ok ? r.json() : Promise.reject()),
      fetch(`${API}/api/v1/public/booking/${slug}/branches`).then(r => r.ok ? r.json() : []).catch(() => []),
    ])
      .then(([biz, br]) => { setBusiness(biz); setBranches(br); })
      .catch(() => setError("İşletme bulunamadı."))
      .finally(() => setLoading(false));
  }, [slug]);

  // Load staff when service selected
  useEffect(() => {
    if (!slug || !selectedService) return;
    let url = `${API}/api/v1/public/booking/${slug}/staff?service_id=${selectedService.id}`;
    if (selectedBranch) url += `&branch_id=${selectedBranch.id}`;
    fetch(url).then(r => r.ok ? r.json() : []).then(setStaffList).catch(() => setStaffList([]));
  }, [slug, selectedService, selectedBranch]);

  // Load slots when date selected
  useEffect(() => {
    if (!slug || !selectedService || !selectedDate) return;
    setSlotsLoading(true);
    setSelectedTime("");
    let url = `${API}/api/v1/public/booking/${slug}/available-slots?date=${selectedDate}&service_id=${selectedService.id}`;
    if (selectedStaff) url += `&staff_id=${selectedStaff.id}`;
    if (selectedBranch) url += `&branch_id=${selectedBranch.id}`;
    fetch(url)
      .then(r => r.ok ? r.json() : { available_slots: [] })
      .then(res => setSlots(res.available_slots || []))
      .catch(() => setSlots([]))
      .finally(() => setSlotsLoading(false));
  }, [slug, selectedService, selectedStaff, selectedBranch, selectedDate]);

  // Book appointment
  const handleBook = async () => {
    if (!slug) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: any = {
        customer_name: form.name,
        customer_phone: form.phone,
        customer_email: form.email || null,
        service_id: selectedService!.id,
        date: selectedDate,
        start_time: selectedTime,
      };
      if (selectedStaff) payload.staff_id = selectedStaff.id;
      if (selectedBranch) payload.branch_id = selectedBranch.id;

      const res = await fetch(`${API}/api/v1/public/booking/${slug}/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Randevu oluşturulamadı.");
      }
      setSuccess(true);
    } catch (e: any) {
      setError(e.message || "Randevu oluşturulamadı. Lütfen tekrar deneyin.");
    } finally {
      setSubmitting(false);
    }
  };

  // Generate next 14 days
  const dateOptions = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() + i + 1);
    return d.toISOString().split("T")[0];
  });

  const canNext = () => {
    switch (step) {
      case 0: return !!selectedService;
      case 1: return true;
      case 2: return !!selectedDate && !!selectedTime;
      case 3: return form.name.trim().length > 1 && form.phone.trim().length > 5;
      default: return true;
    }
  };

  // ─── Loading ───
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-violet-400 mx-auto mb-3" />
          <p className="text-white/40 text-sm">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // ─── Error ───
  if (error && !business) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">😔</span>
          </div>
          <p className="text-red-400 text-lg font-medium">{error}</p>
          <p className="text-white/30 mt-2 text-sm">Bu bağlantı geçersiz veya işletme bulunamadı.</p>
        </div>
      </div>
    );
  }

  // ─── Success ───
  if (success) {
    return (
      <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="relative mx-auto mb-6">
            <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-10 h-10 text-emerald-400" />
            </div>
            <div className="absolute inset-0 w-20 h-20 rounded-full bg-emerald-500/10 animate-ping mx-auto" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Randevunuz Oluşturuldu! 🎉</h1>
          <p className="text-white/50 mb-6 text-sm">
            <strong className="text-white">{formatDate(selectedDate)}</strong> saat <strong className="text-white">{selectedTime}</strong> için randevunuz başarıyla oluşturuldu.
          </p>
          <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 text-left space-y-3 text-sm">
            {[
              { label: "İşletme", value: business?.name },
              { label: "Hizmet", value: selectedService?.name },
              ...(selectedStaff ? [{ label: "Personel", value: selectedStaff.full_name }] : []),
              { label: "Tarih", value: formatDate(selectedDate) },
              { label: "Saat", value: selectedTime },
              { label: "Süre", value: `${selectedService?.duration} dakika` },
            ].map((r, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-white/40">{r.label}</span>
                <span className="text-white font-medium">{r.value}</span>
              </div>
            ))}
            <div className="border-t border-white/5 pt-3 flex justify-between items-center">
              <span className="text-emerald-400 font-medium">Ücret</span>
              <span className="text-emerald-400 font-bold text-lg">{formatCurrency(selectedService?.price || 0)}</span>
            </div>
          </div>
          <div className="mt-5 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3">
            <p className="text-amber-300 text-xs">⏳ Randevunuz onay bekliyor. İşletme tarafından onaylandığında bilgilendirileceksiniz.</p>
          </div>
        </div>
      </div>
    );
  }

  // ─── Main Page ───
  return (
    <div className="min-h-screen bg-[#0a0a1a] text-white relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-violet-600/8 rounded-full blur-[180px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-blue-600/5 rounded-full blur-[150px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 border-b border-white/5 bg-white/[0.02] backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-4 py-5 flex items-center gap-3">
          {business?.logo_url ? (
            <img src={business.logo_url} alt="" className="w-11 h-11 rounded-xl object-cover border border-white/10" />
          ) : (
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-violet-500/20">
              {business?.name?.[0]}
            </div>
          )}
          <div>
            <h1 className="font-bold text-white text-lg">{business?.name}</h1>
            {business?.industry && <p className="text-xs text-white/40">{business.industry}</p>}
          </div>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-violet-300 bg-violet-500/10 border border-violet-500/20 px-3 py-1.5 rounded-full">
            <Sparkles className="w-3 h-3" />
            Online Randevu
          </div>
        </div>
      </header>

      {/* Step Indicator */}
      <div className="relative z-10 max-w-3xl mx-auto px-4 pt-8 pb-6">
        <div className="flex items-center justify-between mb-8">
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center">
              <div className="flex flex-col items-center gap-1.5">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all duration-300 ${
                  i < step ? "bg-emerald-500/20 border-emerald-500 text-emerald-400" :
                  i === step ? "bg-violet-500/20 border-violet-500 text-violet-300 scale-110 shadow-lg shadow-violet-500/20" :
                  "border-white/10 text-white/20"
                }`}>
                  {i < step ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                </div>
                <span className={`text-[10px] font-medium hidden sm:block ${
                  i <= step ? "text-white/60" : "text-white/20"
                }`}>{s}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-6 sm:w-12 lg:w-20 h-0.5 mx-1 sm:mx-2 rounded-full transition-all duration-500 mb-5 sm:mb-5 ${
                  i < step ? "bg-emerald-500/50" : "bg-white/5"
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="bg-white/[0.02] border border-white/8 rounded-2xl p-6 sm:p-8 backdrop-blur-sm min-h-[420px] shadow-2xl shadow-black/20">

          {/* Step 0: Service */}
          {step === 0 && (
            <div>
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2"><Star className="w-5 h-5 text-violet-400" /> Hizmet Seçin</h2>
              <p className="text-white/40 text-sm mb-6">Almak istediğiniz hizmeti seçin.</p>

              {branches.length > 1 && (
                <div className="mb-5">
                  <label className="text-xs font-medium text-white/50 mb-2 block flex items-center gap-1.5"><Building2 className="w-3 h-3" /> Şube</label>
                  <div className="flex flex-wrap gap-2">
                    {branches.map(b => (
                      <button key={b.id} onClick={() => setSelectedBranch(selectedBranch?.id === b.id ? null : b)}
                        className={`px-4 py-2 rounded-lg text-sm border transition-all ${
                          selectedBranch?.id === b.id ? "border-violet-500 bg-violet-500/15 text-violet-300" : "border-white/10 text-white/50 hover:bg-white/5"
                        }`}>
                        {b.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid gap-3">
                {business?.services.map(s => (
                  <button key={s.id}
                    onClick={() => { setSelectedService(s); setSelectedStaff(null); setSelectedDate(""); setSelectedTime(""); }}
                    className={`w-full text-left p-5 rounded-xl border transition-all duration-200 hover:bg-white/[0.03] group ${
                      selectedService?.id === s.id
                        ? "border-violet-500/60 bg-violet-500/10 ring-1 ring-violet-500/20"
                        : "border-white/8 hover:border-white/15"
                    }`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-semibold text-[15px]">{s.name}</p>
                        {s.description && <p className="text-sm text-white/35 mt-1 line-clamp-2">{s.description}</p>}
                        <div className="flex items-center gap-3 mt-2.5">
                          <span className="flex items-center gap-1 text-xs text-white/40 bg-white/5 px-2 py-1 rounded-md">
                            <Clock className="w-3 h-3" />{s.duration} dk
                          </span>
                        </div>
                      </div>
                      <span className="text-violet-400 font-bold text-lg ml-4 whitespace-nowrap">{formatCurrency(s.price)}</span>
                    </div>
                  </button>
                ))}
                {(!business?.services || business.services.length === 0) && (
                  <div className="text-center py-12">
                    <p className="text-white/30">Bu işletmede aktif hizmet bulunamadı.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 1: Staff */}
          {step === 1 && (
            <div>
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2"><User className="w-5 h-5 text-violet-400" /> Personel Seçin</h2>
              <p className="text-white/40 text-sm mb-6">Tercih ettiğiniz personeli seçebilir veya atlayabilirsiniz.</p>

              <button onClick={() => setSelectedStaff(null)}
                className={`w-full text-left p-4 rounded-xl border mb-3 transition-all hover:bg-white/[0.03] ${
                  !selectedStaff ? "border-violet-500/60 bg-violet-500/10 ring-1 ring-violet-500/20" : "border-white/8"
                }`}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                    <User className="w-5 h-5 text-white/30" />
                  </div>
                  <div>
                    <p className="font-semibold">Fark Etmez</p>
                    <p className="text-xs text-white/35">Uygun herhangi bir personel atansın</p>
                  </div>
                </div>
              </button>

              <div className="grid gap-3">
                {staffList.map(s => (
                  <button key={s.id} onClick={() => setSelectedStaff(s)}
                    className={`w-full text-left p-4 rounded-xl border transition-all hover:bg-white/[0.03] ${
                      selectedStaff?.id === s.id
                        ? "border-violet-500/60 bg-violet-500/10 ring-1 ring-violet-500/20"
                        : "border-white/8"
                    }`}>
                    <div className="flex items-center gap-3">
                      {s.avatar_url ? (
                        <img src={s.avatar_url} alt="" className="w-10 h-10 rounded-full object-cover border border-white/10" />
                      ) : (
                        <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm"
                          style={{ background: `linear-gradient(135deg, ${s.color || '#8b5cf6'}, ${s.color || '#3b82f6'}80)` }}>
                          {s.full_name?.[0]}
                        </div>
                      )}
                      <div>
                        <p className="font-semibold">{s.full_name}</p>
                        {s.title && <p className="text-xs text-white/35">{s.title}</p>}
                      </div>
                    </div>
                  </button>
                ))}
                {staffList.length === 0 && (
                  <p className="text-white/30 text-center py-4 text-sm">Bu hizmet için kayıtlı personel bulunamadı.</p>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Date & Time */}
          {step === 2 && (
            <div>
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2"><Calendar className="w-5 h-5 text-violet-400" /> Tarih & Saat</h2>
              <p className="text-white/40 text-sm mb-6">Uygun bir tarih ve saat belirleyin.</p>

              <div className="mb-6">
                <label className="text-xs font-medium text-white/50 mb-3 block">Tarih Seçin</label>
                <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
                  {dateOptions.map(d => {
                    const dt = new Date(d);
                    const dayName = dt.toLocaleDateString("tr-TR", { weekday: "short" });
                    const dayNum = dt.getDate();
                    const month = dt.toLocaleDateString("tr-TR", { month: "short" });
                    const isWeekend = dt.getDay() === 0 || dt.getDay() === 6;
                    return (
                      <button key={d} onClick={() => setSelectedDate(d)}
                        className={`p-2.5 rounded-xl border text-center transition-all duration-200 hover:bg-white/5 ${
                          selectedDate === d
                            ? "border-violet-500 bg-violet-500/15 ring-1 ring-violet-500/20 shadow-lg shadow-violet-500/10"
                            : isWeekend ? "border-white/5 text-white/30" : "border-white/8"
                        }`}>
                        <p className="text-[10px] uppercase text-white/35 font-medium">{dayName}</p>
                        <p className="text-lg font-bold my-0.5">{dayNum}</p>
                        <p className="text-[10px] text-white/30">{month}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {selectedDate && (
                <div>
                  <label className="text-xs font-medium text-white/50 mb-3 block flex items-center gap-1.5">
                    <Clock className="w-3 h-3" /> Müsait Saatler
                  </label>
                  {slotsLoading ? (
                    <div className="flex items-center justify-center py-10">
                      <Loader2 className="w-6 h-6 animate-spin text-violet-400" />
                    </div>
                  ) : slots.length === 0 ? (
                    <div className="text-center py-10 bg-white/[0.02] rounded-xl border border-white/5">
                      <p className="text-white/30 text-sm">😔 Bu tarihte müsait saat bulunamadı.</p>
                      <p className="text-white/20 text-xs mt-1">Lütfen başka bir tarih deneyin.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2">
                      {slots.map(t => {
                        const display = typeof t === "string" ? t.substring(0, 5) : String(t).substring(0, 5);
                        return (
                          <button key={t} onClick={() => setSelectedTime(display)}
                            className={`py-2.5 rounded-lg border text-sm font-medium transition-all duration-200 hover:bg-white/5 ${
                              selectedTime === display
                                ? "border-violet-500 bg-violet-500/15 text-violet-300 ring-1 ring-violet-500/20 shadow-lg shadow-violet-500/10"
                                : "border-white/8 text-white/60"
                            }`}>
                            {display}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Step 3: Contact Info */}
          {step === 3 && (
            <div>
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2"><Mail className="w-5 h-5 text-violet-400" /> Bilgileriniz</h2>
              <p className="text-white/40 text-sm mb-6">Randevunuz için iletişim bilgilerinizi girin.</p>
              <div className="space-y-5 max-w-md">
                <div>
                  <label className="text-xs font-medium text-white/50 mb-2 flex items-center gap-1.5 block">
                    <User className="w-3 h-3" />Ad Soyad <span className="text-red-400">*</span>
                  </label>
                  <input className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-white/15 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/50 transition-all"
                    value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Adınızı ve soyadınızı girin" />
                </div>
                <div>
                  <label className="text-xs font-medium text-white/50 mb-2 flex items-center gap-1.5 block">
                    <Phone className="w-3 h-3" />Telefon <span className="text-red-400">*</span>
                  </label>
                  <input className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-white/15 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/50 transition-all"
                    value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="05XX XXX XX XX" />
                </div>
                <div>
                  <label className="text-xs font-medium text-white/50 mb-2 flex items-center gap-1.5 block">
                    <Mail className="w-3 h-3" />E-posta <span className="text-white/20">(isteğe bağlı)</span>
                  </label>
                  <input type="email" className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-white/15 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/50 transition-all"
                    value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="ornek@email.com" />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Confirm */}
          {step === 4 && (
            <div>
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-emerald-400" /> Randevu Özeti</h2>
              <p className="text-white/40 text-sm mb-6">Bilgilerinizi kontrol edin ve onaylayın.</p>
              <div className="space-y-2.5 max-w-lg">
                {[
                  { icon: Star, label: "Hizmet", value: selectedService?.name, color: "text-violet-400" },
                  { icon: User, label: "Personel", value: selectedStaff?.full_name || "Fark Etmez", color: "text-blue-400" },
                  { icon: Calendar, label: "Tarih", value: selectedDate ? formatDate(selectedDate) : "", color: "text-amber-400" },
                  { icon: Clock, label: "Saat", value: selectedTime, color: "text-cyan-400" },
                  { icon: Clock, label: "Süre", value: `${selectedService?.duration} dakika`, color: "text-white/40" },
                  { icon: User, label: "Ad Soyad", value: form.name, color: "text-white/40" },
                  { icon: Phone, label: "Telefon", value: form.phone, color: "text-white/40" },
                  ...(form.email ? [{ icon: Mail, label: "E-posta", value: form.email, color: "text-white/40" }] : []),
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-colors">
                    <span className="text-white/40 text-sm flex items-center gap-2">
                      <item.icon className={`w-3.5 h-3.5 ${item.color}`} />{item.label}
                    </span>
                    <span className="text-white font-medium text-sm text-right max-w-[60%] truncate">{item.value}</span>
                  </div>
                ))}

                <div className="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-violet-500/10 to-blue-500/10 border border-violet-500/20 mt-4">
                  <span className="text-violet-300 font-semibold">Toplam Ücret</span>
                  <span className="text-violet-300 font-bold text-2xl">{formatCurrency(selectedService?.price || 0)}</span>
                </div>
              </div>
              {error && (
                <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-6 px-1">
          <button onClick={() => { setStep(s => s - 1); setError(null); }}
            disabled={step === 0}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10 transition-all disabled:opacity-0 disabled:pointer-events-none">
            <ChevronLeft className="w-4 h-4" /> Geri
          </button>

          {step < 4 ? (
            <button onClick={() => setStep(s => s + 1)}
              disabled={!canNext()}
              className="flex items-center gap-2 px-7 py-3 rounded-xl text-sm font-semibold bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 transition-all disabled:opacity-20 disabled:cursor-not-allowed shadow-xl shadow-violet-500/15 hover:shadow-violet-500/25 hover:scale-[1.02] active:scale-[0.98]">
              İleri <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={handleBook}
              disabled={submitting}
              className="flex items-center gap-2 px-8 py-3 rounded-xl text-sm font-semibold bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 transition-all disabled:opacity-50 shadow-xl shadow-emerald-500/15 hover:shadow-emerald-500/25 hover:scale-[1.02] active:scale-[0.98]">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Randevuyu Onayla
            </button>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 mt-16 py-5">
        <p className="text-center text-white/15 text-xs">
          Powered by <span className="text-violet-400/60 font-medium">BusinessOS</span>
        </p>
      </footer>
    </div>
  );
}
