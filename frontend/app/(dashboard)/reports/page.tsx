"use client";

import { useState, useEffect, useMemo } from "react";
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths, startOfYear, endOfYear } from "date-fns";
import { tr } from "date-fns/locale";
import { BarChart3, TrendingUp, TrendingDown, Users, CalendarCheck, CalendarClock, Clock, UserCog, Wallet } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import { getActiveBusinessId } from "@/lib/business";
import {
  getRevenueReport,
  getAppointmentReport,
  getCustomerReport,
  getStaffPerformanceReport
} from "@/lib/api";
import type { RevenueDataPoint, AppointmentReport, CustomerReport, StaffPerformance } from "@/types/reports";
import { formatCurrency } from "@/lib/utils";
import { toast } from "sonner";

const COLORS = {
  income: "#22c55e",
  expense: "#ef4444",
  net: "#3b82f6",
  appointments: "var(--agent-appointments)",
  customers: "var(--accent)",
};

const TABS = [
  { id: "revenue", label: "Gelir Raporu" },
  { id: "appointments", label: "Randevu Raporu" },
  { id: "customers", label: "Müşteri Raporu" },
  { id: "staff", label: "Personel Performansı" },
];

const PRESETS = [
  { label: "Bu Hafta", getValue: () => ({ start: startOfWeek(new Date(), { weekStartsOn: 1 }), end: endOfWeek(new Date(), { weekStartsOn: 1 }) }) },
  { label: "Bu Ay", getValue: () => ({ start: startOfMonth(new Date()), end: endOfMonth(new Date()) }) },
  { label: "Son 3 Ay", getValue: () => ({ start: subMonths(new Date(), 3), end: new Date() }) },
  { label: "Son 6 Ay", getValue: () => ({ start: subMonths(new Date(), 6), end: new Date() }) },
  { label: "Bu Yıl", getValue: () => ({ start: startOfYear(new Date()), end: endOfYear(new Date()) }) },
];

export default function ReportsPage() {
  const businessId = getActiveBusinessId();

  const [activeTab, setActiveTab] = useState("revenue");
  const [startDate, setStartDate] = useState(() => format(startOfMonth(new Date()), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(() => format(endOfMonth(new Date()), 'yyyy-MM-dd'));
  const [groupBy, setGroupBy] = useState("day");

  const [loading, setLoading] = useState(false);
  
  // Data States
  const [revenueData, setRevenueData] = useState<RevenueDataPoint[]>([]);
  const [appointmentData, setAppointmentData] = useState<AppointmentReport | null>(null);
  const [customerData, setCustomerData] = useState<CustomerReport | null>(null);
  const [staffData, setStaffData] = useState<StaffPerformance[]>([]);

  useEffect(() => {
    if (!businessId) return;
    fetchData();
  }, [businessId, activeTab, startDate, endDate, groupBy]);

  const fetchData = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      if (activeTab === "revenue") {
        const data = await getRevenueReport(businessId, startDate, endDate, groupBy);
        setRevenueData(data);
      } else if (activeTab === "appointments") {
        const data = await getAppointmentReport(businessId, startDate, endDate);
        setAppointmentData(data);
      } else if (activeTab === "customers") {
        const data = await getCustomerReport(businessId, startDate, endDate);
        setCustomerData(data);
      } else if (activeTab === "staff") {
        const data = await getStaffPerformanceReport(businessId, startDate, endDate);
        setStaffData(data);
      }
    } catch (error) {
      toast.error("Rapor verileri alınırken hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const preset = PRESETS.find(p => p.label === e.target.value);
    if (preset) {
      const { start, end } = preset.getValue();
      setStartDate(format(start, 'yyyy-MM-dd'));
      setEndDate(format(end, 'yyyy-MM-dd'));
    }
  };

  const totalIncome = revenueData.reduce((acc, curr) => acc + curr.income, 0);
  const totalExpense = revenueData.reduce((acc, curr) => acc + curr.expense, 0);
  const netIncome = totalIncome - totalExpense;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="flex items-center gap-2 font-display text-2xl font-semibold tracking-tight text-ink">
            <BarChart3 className="h-6 w-6 text-[var(--agent-finance)]" />
            Raporlar
          </h1>
          <p className="text-sm text-ink-muted">İşletme performansını detaylı olarak analiz et.</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Select onChange={handlePresetChange} className="h-9" defaultValue="">
              <option value="" disabled>Hızlı Seçim</option>
              {PRESETS.map((preset) => (
                <option key={preset.label} value={preset.label}>{preset.label}</option>
              ))}
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              className="w-auto h-9" 
            />
            <span className="text-ink-muted">-</span>
            <Input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="w-auto h-9" 
            />
          </div>
        </div>
      </div>

      <div className="flex border-b border-white/10">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id 
                ? "border-[var(--agent-finance)] text-ink" 
                : "border-transparent text-ink-muted hover:text-ink hover:border-white/20"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-ink-muted">Rapor yükleniyor...</p>}

      {!loading && activeTab === "revenue" && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Label>Gruplama:</Label>
            <Select 
              value={groupBy} 
              onChange={(e) => setGroupBy(e.target.value)}
              className="w-32 h-9"
            >
              <option value="day">Günlük</option>
              <option value="week">Haftalık</option>
              <option value="month">Aylık</option>
            </Select>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.income }}>
              <CardContent className="flex items-center gap-3 p-4">
                <TrendingUp className="h-5 w-5" style={{ color: COLORS.income }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(totalIncome)}</p>
                  <p className="text-xs text-ink-muted">Toplam Gelir</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.expense }}>
              <CardContent className="flex items-center gap-3 p-4">
                <TrendingDown className="h-5 w-5" style={{ color: COLORS.expense }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(totalExpense)}</p>
                  <p className="text-xs text-ink-muted">Toplam Gider</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: netIncome >= 0 ? COLORS.income : COLORS.expense }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Wallet className="h-5 w-5" style={{ color: netIncome >= 0 ? COLORS.income : COLORS.expense }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(netIncome)}</p>
                  <p className="text-xs text-ink-muted">Net Kâr</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-surface-elevated/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-base">Gelir - Gider Özeti</CardTitle>
            </CardHeader>
            <CardContent className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={revenueData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.income} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={COLORS.income} stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.expense} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={COLORS.expense} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                  <XAxis dataKey="period" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₺${val}`} />
                  <Tooltip 
                    formatter={(value: number, name: string) => [formatCurrency(value), name === 'income' ? 'Gelir' : 'Gider']}
                    contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Area type="monotone" dataKey="income" name="Gelir" stroke={COLORS.income} fillOpacity={1} fill="url(#colorIncome)" />
                  <Area type="monotone" dataKey="expense" name="Gider" stroke={COLORS.expense} fillOpacity={1} fill="url(#colorExpense)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && activeTab === "appointments" && appointmentData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.appointments }}>
              <CardContent className="flex items-center gap-3 p-4">
                <CalendarCheck className="h-5 w-5" style={{ color: COLORS.appointments }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{appointmentData.total_appointments}</p>
                  <p className="text-xs text-ink-muted">Toplam Randevu</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.income }}>
              <CardContent className="flex items-center gap-3 p-4">
                <CalendarCheck className="h-5 w-5" style={{ color: COLORS.income }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{appointmentData.completed_count}</p>
                  <p className="text-xs text-ink-muted">Tamamlanan</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.expense }}>
              <CardContent className="flex items-center gap-3 p-4">
                <CalendarClock className="h-5 w-5" style={{ color: COLORS.expense }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{appointmentData.cancelled_count}</p>
                  <p className="text-xs text-ink-muted">İptal Edilen</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.appointments }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Clock className="h-5 w-5" style={{ color: COLORS.appointments }} />
                <div>
                  <p className="text-xl font-semibold text-ink">%{appointmentData.completion_rate.toFixed(1)}</p>
                  <p className="text-xs text-ink-muted">Tamamlanma Oranı</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Hizmet Bazlı Randevular</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-white/10 text-ink-muted">
                    <tr>
                      <th className="pb-2 font-medium">Hizmet Adı</th>
                      <th className="pb-2 font-medium">Randevu Sayısı</th>
                      <th className="pb-2 font-medium">Gelir</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {appointmentData.by_service.map((service, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="py-2 text-ink">{service.name}</td>
                        <td className="py-2 text-ink">{service.booking_count}</td>
                        <td className="py-2 text-ink">{formatCurrency(service.revenue)}</td>
                      </tr>
                    ))}
                    {appointmentData.by_service.length === 0 && (
                      <tr>
                        <td colSpan={3} className="py-4 text-center text-ink-muted">Kayıt bulunamadı.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && activeTab === "customers" && customerData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card className="border-l-2" style={{ borderLeftColor: COLORS.customers }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Users className="h-5 w-5" style={{ color: COLORS.customers }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{customerData.new_customers_count}</p>
                  <p className="text-xs text-ink-muted">Yeni Müşteriler</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "var(--agent-sales)" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Users className="h-5 w-5" style={{ color: "var(--agent-sales)" }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{customerData.returning_customers_count}</p>
                  <p className="text-xs text-ink-muted">Geri Dönen Müşteriler</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Müşteri Büyümesi</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={customerData.customer_growth} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                    <XAxis dataKey="month" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
                    />
                    <Line type="monotone" dataKey="count" name="Müşteri Sayısı" stroke={COLORS.customers} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">En İyi Müşteriler</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-white/10 text-ink-muted">
                      <tr>
                        <th className="pb-2 font-medium">Müşteri</th>
                        <th className="pb-2 font-medium">Ziyaret</th>
                        <th className="pb-2 font-medium">Toplam Harcama</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {customerData.top_customers.map((c, idx) => (
                        <tr key={idx} className="hover:bg-white/5">
                          <td className="py-2 text-ink">{c.name}</td>
                          <td className="py-2 text-ink">{c.visit_count}</td>
                          <td className="py-2 text-ink">{formatCurrency(c.total_spent)}</td>
                        </tr>
                      ))}
                      {customerData.top_customers.length === 0 && (
                        <tr>
                          <td colSpan={3} className="py-4 text-center text-ink-muted">Kayıt bulunamadı.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {!loading && activeTab === "staff" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Personel Performansı</CardTitle>
            <CardDescription>Personel bazında randevu ve gelir performansı</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-white/10 text-ink-muted">
                  <tr>
                    <th className="pb-2 font-medium">Personel</th>
                    <th className="pb-2 font-medium">Ünvan</th>
                    <th className="pb-2 font-medium">Randevu Sayısı</th>
                    <th className="pb-2 font-medium">Gelir</th>
                    <th className="pb-2 font-medium">Tamamlanma Oranı</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {staffData.map((staff, idx) => {
                    let rateColor = "text-red-400";
                    if (staff.completion_rate >= 80) rateColor = "text-green-400";
                    else if (staff.completion_rate >= 50) rateColor = "text-yellow-400";

                    return (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="py-2 font-medium text-ink">{staff.name}</td>
                        <td className="py-2 text-ink-muted">{staff.title || "-"}</td>
                        <td className="py-2 text-ink">{staff.appointment_count}</td>
                        <td className="py-2 text-ink">{formatCurrency(staff.revenue)}</td>
                        <td className={`py-2 font-medium ${rateColor}`}>%{staff.completion_rate.toFixed(1)}</td>
                      </tr>
                    );
                  })}
                  {staffData.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-ink-muted">Kayıt bulunamadı.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
