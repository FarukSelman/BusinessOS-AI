"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  CalendarCheck,
  ShoppingBag,
  FileText,
  MessagesSquare,
  CalendarClock,
  LineChart,
  Megaphone,
  Clock,
  Sparkles,
  TrendingUp,
  TrendingDown,
  UserCog,
  Wallet,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  listCustomers,
  listAppointments,
  listAppointmentsByDate,
  listServices,
  listDocuments,
  type BusinessService,
  ApiError,
  getDashboardStats,
  getBusiness,
} from "@/lib/api";
import { DashboardStats } from "@/types/reports";
import { formatCurrency } from "@/lib/utils";
import { getActiveBusinessId } from "@/lib/business";
import {
  WeeklyAppointmentsChart,
  RevenueOverviewChart,
  StatusDistributionChart,
  ServicePopularityChart
} from "@/components/dashboard/charts";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

const agentLinks = [
  {
    href: "/support",
    title: "Müşteri destek ajanı",
    desc: "Müşteri sorularını yanıtlar",
    icon: MessagesSquare,
    color: "var(--agent-support)",
  },
  {
    href: "/appointments",
    title: "Randevu ajanı",
    desc: "Takvimi yönetir",
    icon: CalendarClock,
    color: "var(--agent-appointments)",
  },
  {
    href: "/sales",
    title: "Satış ve öneri ajanı",
    desc: "Ürün önerir",
    icon: ShoppingBag,
    color: "var(--agent-sales)",
  },
  {
    href: "/finance",
    title: "Finansal analiz",
    desc: "İşletme verilerini analiz eder",
    icon: LineChart,
    color: "var(--agent-finance)",
  },
  {
    href: "/marketing",
    title: "Pazarlama ajanı",
    desc: "Kampanya önerir",
    icon: Megaphone,
    color: "var(--agent-marketing)",
  },
];

export default function DashboardHomePage() {
  const businessId = getActiveBusinessId();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCustomers, setActiveCustomers] = useState(0);
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [allAppointments, setAllAppointments] = useState<Appointment[]>([]);
  const [activeServices, setActiveServices] = useState(0);
  const [servicesData, setServicesData] = useState<BusinessService[]>([]);
  const [documentsReady, setDocumentsReady] = useState({ ready: 0, total: 0 });
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [businessSlug, setBusinessSlug] = useState<string | null>(null);
  const [linkCopied, setLinkCopied] = useState(false);

  const confirmedToday = todayAppointments.filter((appointment) =>
    appointment.status === "CONFIRMED" || appointment.status === "PENDING"
  );
  const availableSlotsEstimate = Math.max(0, 9 - confirmedToday.length);

  useEffect(() => {
    if (!businessId) {
      setError("Aktif işletme bulunamadı.");
      setLoading(false);
      return;
    }
    Promise.allSettled([
      listCustomers(businessId),
      listAppointments(businessId, 1, 100),
      listAppointmentsByDate(businessId, todayISO()),
      listServices(businessId),
      listDocuments(businessId),
      getDashboardStats(businessId),
      getBusiness(businessId),
    ])
      .then((results) => {
        if (results[0].status === "fulfilled") {
          setActiveCustomers(results[0].value.filter((c) => c.status === "ACTIVE").length);
        }
        if (results[1].status === "fulfilled") {
          setAllAppointments(results[1].value);
        }
        if (results[2].status === "fulfilled") {
          setTodayAppointments(results[2].value);
        }
        if (results[3].status === "fulfilled") {
          setActiveServices(results[3].value.filter((s) => s.status === "ACTIVE").length);
          setServicesData(results[3].value);
        }
        if (results[4].status === "fulfilled") {
          setDocumentsReady({
            ready: results[4].value.filter((d) => d.status === "READY").length,
            total: results[4].value.length,
          });
        }
        if (results[5].status === "fulfilled") {
          setStats(results[5].value);
        }
        if (results[6].status === "fulfilled") {
          setBusinessSlug(results[6].value.slug);
        }
      })
      .catch((err) => setError("Veriler yüklenirken beklenmeyen bir hata oluştu."))
      .finally(() => setLoading(false));
  }, [businessId]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Genel bakış</h1>
        <p className="text-sm text-ink-muted">İşletmenin tüm ajanlarına buradan göz atabilirsin.</p>
      </div>

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>}

      {loading ? (
        <p className="text-sm text-ink-muted">Yükleniyor...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Row 1 */}
            <Card className="border-l-2" style={{ borderLeftColor: "var(--accent)" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Users className="h-5 w-5 text-accent" />
                <div>
                  <p className="text-2xl font-semibold text-ink">{stats?.total_customers ?? activeCustomers}</p>
                  <p className="text-xs text-ink-muted">Toplam Müşteri</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "var(--agent-appointments)" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <CalendarCheck className="h-5 w-5" style={{ color: "var(--agent-appointments)" }} />
                <div>
                  <p className="text-2xl font-semibold text-ink">{stats?.total_appointments_today ?? todayAppointments.length}</p>
                  <p className="text-xs text-ink-muted">Bugünkü Randevular</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "var(--agent-appointments)" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <CalendarClock className="h-5 w-5" style={{ color: "var(--agent-appointments)" }} />
                <div>
                  <p className="text-2xl font-semibold text-ink">{stats?.total_appointments_this_month ?? 0}</p>
                  <p className="text-xs text-ink-muted">Bu Ay Randevular</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "#f59e0b" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Clock className="h-5 w-5" style={{ color: "#f59e0b" }} />
                <div>
                  <p className="text-2xl font-semibold text-ink">{stats?.pending_appointments ?? 0}</p>
                  <p className="text-xs text-ink-muted">Bekleyen Randevular</p>
                </div>
              </CardContent>
            </Card>

            {/* Row 2 */}
            <Card className="border-l-2" style={{ borderLeftColor: "#22c55e" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <TrendingUp className="h-5 w-5" style={{ color: "#22c55e" }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(stats?.total_revenue_this_month ?? 0)}</p>
                  <p className="text-xs text-ink-muted">Bu Ay Gelir</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "#ef4444" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <TrendingDown className="h-5 w-5" style={{ color: "#ef4444" }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(stats?.total_expenses_this_month ?? 0)}</p>
                  <p className="text-xs text-ink-muted">Bu Ay Gider</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: (stats?.net_profit_this_month ?? 0) >= 0 ? "#22c55e" : "#ef4444" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <Wallet className="h-5 w-5" style={{ color: (stats?.net_profit_this_month ?? 0) >= 0 ? "#22c55e" : "#ef4444" }} />
                <div>
                  <p className="text-xl font-semibold text-ink">{formatCurrency(stats?.net_profit_this_month ?? 0)}</p>
                  <p className="text-xs text-ink-muted">Net Kâr</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-l-2" style={{ borderLeftColor: "var(--accent)" }}>
              <CardContent className="flex items-center gap-3 p-4">
                <UserCog className="h-5 w-5 text-accent" />
                <div>
                  <p className="text-2xl font-semibold text-ink">{stats?.active_staff_count ?? 0}</p>
                  <p className="text-xs text-ink-muted">Aktif Personel</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Online Booking Link */}
          {businessSlug && (
            <Card className="border border-violet-500/20 bg-gradient-to-r from-violet-500/5 to-blue-500/5">
              <CardContent className="flex items-center gap-3 p-4">
                <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-violet-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-ink-muted font-medium">Online Randevu Linki</p>
                  <p className="text-sm text-ink font-mono truncate">{typeof window !== 'undefined' ? `${window.location.origin}/book/${businessSlug}` : `/book/${businessSlug}`}</p>
                </div>
                <button
                  onClick={() => {
                    const url = `${window.location.origin}/book/${businessSlug}`;
                    navigator.clipboard.writeText(url).then(() => {
                      setLinkCopied(true);
                      setTimeout(() => setLinkCopied(false), 2000);
                    });
                  }}
                  className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 transition-colors"
                >
                  {linkCopied ? "✓ Kopyalandı" : "Kopyala"}
                </button>
              </CardContent>
            </Card>
          )}

          <Card className="border-l-4 border-l-[var(--agent-marketing)] bg-gradient-to-r from-[color-mix(in_srgb,var(--agent-marketing)_10%,transparent)] to-surface">
            <CardHeader className="flex-row items-start gap-3 space-y-0 pb-3">
              <Sparkles className="mt-0.5 h-5 w-5 text-[var(--agent-marketing)]" />
              <div>
                <CardTitle className="text-base">Günlük AI özeti</CardTitle>
                <CardDescription>Bugünün verilerine göre önceliklerin</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="grid gap-2 pt-0 text-sm text-ink-muted sm:grid-cols-3">
              <p><span className="font-medium text-ink">{confirmedToday.length} randevu</span> bugün planlandı.</p>
              <p><span className="font-medium text-ink">Yaklaşık {availableSlotsEstimate} boş saat</span> için kampanya fırsatı var.</p>
              <p>{documentsReady.total === 0 ? "Bilgi tabanı henüz boş; AI yanıtlarını güçlendirmek için belge yükleyebilirsin." : `${documentsReady.ready} bilgi kaynağı AI tarafından kullanılmaya hazır.`}</p>
            </CardContent>
          </Card>

          {todayAppointments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Bugünkü randevular</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 pt-0">
                {todayAppointments
                  .slice()
                  .sort((a, b) => a.start_time.localeCompare(b.start_time))
                  .slice(0, 5)
                  .map((a) => (
                    <div key={a.id} className="flex items-center gap-3 text-sm">
                      <Clock className="h-3.5 w-3.5 text-ink-muted" />
                      <span className="font-medium text-ink">{a.start_time.slice(0, 5)}</span>
                      <span className="text-ink-muted">{a.customer_name}</span>
                    </div>
                  ))}
                {todayAppointments.length > 5 && (
                  <Link href="/appointments" className="text-xs text-accent underline">
                    Tümünü gör ({todayAppointments.length})
                  </Link>
                )}
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card className="bg-surface-elevated/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-base">Haftalık Randevu Trendi</CardTitle>
                <CardDescription>Son 7 günün randevu sayıları</CardDescription>
              </CardHeader>
              <CardContent>
                <WeeklyAppointmentsChart appointments={allAppointments} />
              </CardContent>
            </Card>

            <Card className="bg-surface-elevated/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-base">Gelir Dağılımı</CardTitle>
                <CardDescription>Hizmetlere göre tamamlanan randevu gelirleri</CardDescription>
              </CardHeader>
              <CardContent>
                <RevenueOverviewChart appointments={allAppointments} services={servicesData} />
              </CardContent>
            </Card>

            <Card className="bg-surface-elevated/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-base">Randevu Durumları</CardTitle>
                <CardDescription>Tüm randevuların güncel durumları</CardDescription>
              </CardHeader>
              <CardContent>
                <StatusDistributionChart appointments={allAppointments} />
              </CardContent>
            </Card>

            <Card className="bg-surface-elevated/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-base">En Popüler Hizmetler</CardTitle>
                <CardDescription>En çok tercih edilen 5 hizmet</CardDescription>
              </CardHeader>
              <CardContent>
                <ServicePopularityChart appointments={allAppointments} services={servicesData} />
              </CardContent>
            </Card>
          </div>
        </>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-ink-muted">Ajanlar</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {agentLinks.map((a) => (
            <Link key={a.href} href={a.href}>
              <Card
                className="border-l-2 transition-colors hover:border-r-2"
                style={{ borderLeftColor: a.color }}
              >
                <CardHeader className="flex-row items-center gap-3 space-y-0">
                  <a.icon className="h-5 w-5 shrink-0" style={{ color: a.color }} />
                  <div>
                    <CardTitle className="text-base">{a.title}</CardTitle>
                    <CardDescription>{a.desc}</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
