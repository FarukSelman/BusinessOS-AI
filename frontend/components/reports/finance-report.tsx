"use client";

import { useEffect, useState, type ReactNode } from "react";
import { format } from "date-fns";
import { tr } from "date-fns/locale";
import { ArrowDownRight, ArrowUpRight, Download, Info, Minus } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  LabelList,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ApiError, getFinanceReport } from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { fromISODate } from "@/lib/date";
import { exportToCSV } from "@/lib/export";
import { formatCurrency } from "@/lib/utils";
import type { FinanceGroup, FinancePeriod, FinanceReport as Report } from "@/types/reports";

// Seri renkleri tema değişkenlerinden (globals.css --chart-*): koyu temada daha parlak tonlar.
const SOURCES = [
  { key: "invoices", label: "Faturalar", color: "var(--chart-1)" },
  { key: "product_sales", label: "Ürün satışları", color: "var(--chart-5)" },
  { key: "installments", label: "Paket taksitleri", color: "var(--chart-6)" },
  { key: "other_income", label: "Elle girilen gelir", color: "var(--chart-3)" },
] as const;
const EXPENSE = { label: "Gider", color: "var(--chart-4)" };
const NET = { label: "Net kâr", color: "var(--chart-7)" };

const GROUP_LABELS: Record<FinanceGroup, string> = { day: "Günlük", week: "Haftalık", month: "Aylık" };

const tooltipStyle = {
  backgroundColor: "var(--surface-elevated)",
  borderColor: "var(--border)",
  borderRadius: "8px",
  color: "var(--ink)",
};
const legendText = (value: string) => <span style={{ color: "var(--ink)" }}>{value}</span>;

const compact = new Intl.NumberFormat("tr-TR", { notation: "compact", maximumFractionDigits: 1 });
const axisMoney = (v: number) => `${v < 0 ? "−" : ""}₺${compact.format(Math.abs(v))}`;
/** CSV için: Türkçe Excel'in okuduğu ondalık virgüllü sayı, para birimi işareti olmadan. */
const csvNumber = (v: number) => v.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function periodLabel(period: string, group: FinanceGroup, long = false): string {
  const d = fromISODate(period);
  if (group === "month") return format(d, long ? "LLLL yyyy" : "LLL yyyy", { locale: tr });
  if (group === "week") return `${format(d, "d MMM", { locale: tr })} haftası`;
  return format(d, long ? "d MMMM yyyy, EEEE" : "d MMM", { locale: tr });
}

/**
 * Raporlar sayfasının Finans sekmesi (yalnızca sahip/yönetici). Tarih aralığı
 * sayfadan gelir; gruplama burada seçilir. Her grafik tablo olarak da açılır ve
 * CSV indirilebilir (exportToCSV formül enjeksiyonuna karşı hücreleri kaçışlar).
 */
export function FinanceReport({ startDate, endDate }: { startDate: string; endDate: string }) {
  const businessId = getActiveBusinessId();
  const [group, setGroup] = useState<FinanceGroup>("day");
  const [state, setState] = useState<{ key: string; report: Report | null; error: string | null } | null>(null);
  const key = `${startDate}|${endDate}|${group}`;

  useEffect(() => {
    if (!businessId) return;
    const controller = new AbortController();
    getFinanceReport(businessId, startDate, endDate, group, controller.signal)
      .then((report) => setState({ key, report, error: null }))
      .catch((err) => {
        if (controller.signal.aborted) return;
        setState({ key, report: null, error: err instanceof ApiError ? err.message : "Finans raporu yüklenemedi." });
      });
    return () => controller.abort();
  }, [businessId, startDate, endDate, group, key]);

  const loading = state?.key !== key;
  const report = !loading ? state?.report ?? null : null;
  const error = !loading ? state?.error ?? null : null;
  const dailyTooLong = error?.startsWith("Günlük gruplama");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Label htmlFor="finance-group">Gruplama:</Label>
        <Select id="finance-group" value={group} onChange={(e) => setGroup(e.target.value as FinanceGroup)} className="h-9 w-32">
          {(Object.keys(GROUP_LABELS) as FinanceGroup[]).map((g) => (
            <option key={g} value={g}>{GROUP_LABELS[g]}</option>
          ))}
        </Select>
      </div>

      {loading && <p className="text-sm text-ink-muted">Finans raporu yükleniyor...</p>}

      {error && (
        <div role="alert" className="rounded-lg border border-border bg-surface-elevated p-4 text-sm">
          <p className="text-ink">{error}</p>
          {dailyTooLong && (
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="self-center text-ink-muted">Önerilen:</span>
              <Button size="sm" variant="outline" onClick={() => setGroup("week")}>Haftalık göster</Button>
              <Button size="sm" variant="outline" onClick={() => setGroup("month")}>Aylık göster</Button>
            </div>
          )}
        </div>
      )}

      {report && <ReportBody report={report} />}
    </div>
  );
}

function ReportBody({ report }: { report: Report }) {
  const group = report.group_by;
  const range = `${report.start_date}_${report.end_date}`;
  const totalExpense = report.expense_by_category.reduce((s, r) => s + r.amount, 0);
  const trend = report.series.map((p) => ({ ...p, label: periodLabel(p.period, group) }));

  return (
    <>
      <ComparisonCards report={report} />

      <ChartCard
        title="Gelir ve gider trendi"
        description={`${GROUP_LABELS[group]} gelir (kaynaklara göre), gider ve net kâr.`}
        csv={{
          name: `Finans_trend_${range}`,
          headers: ["Dönem", ...SOURCES.map((s) => s.label), "Toplam gelir", "Gider", "Net kâr"],
          rows: report.series.map((p) => [
            periodLabel(p.period, group, true),
            ...SOURCES.map((s) => csvNumber(p[s.key])),
            csvNumber(p.income), csvNumber(p.expense), csvNumber(p.net),
          ]),
        }}
        table={<TrendTable series={report.series} group={group} />}
        note={
          <>
            Gelir kaynakları birbirini otomatik oluşturmuyor ve ayrı gösteriliyor. Elle girilen gelir, aynı tutar
            için kesilmiş bir faturayla çakışıyorsa iki kez sayılabilir.
          </>
        }
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={trend} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
            <XAxis dataKey="label" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false}
                   minTickGap={16} interval="preserveStartEnd" />
            <YAxis stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} width={56}
                   tickFormatter={axisMoney} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--border)", opacity: 0.3 }}
                     formatter={(value: number, name: string) => [formatCurrency(value), name]} />
            <Legend wrapperStyle={{ fontSize: "12px" }} formatter={legendText} />
            {SOURCES.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} stackId="income" fill={s.color} maxBarSize={40} />
            ))}
            <Bar dataKey="expense" name={EXPENSE.label} fill={EXPENSE.color} maxBarSize={40} />
            <Line type="monotone" dataKey="net" name={NET.label} stroke={NET.color} strokeWidth={2}
                  dot={{ r: 3 }} activeDot={{ r: 5 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <RankedBars
          title="Gider kategorileri"
          empty="Bu aralıkta gider yok."
          rows={report.expense_by_category.map((r) => ({
            name: r.name,
            amount: r.amount,
            detail: totalExpense > 0 ? `%${((r.amount / totalExpense) * 100).toLocaleString("tr-TR", { maximumFractionDigits: 1 })}` : "",
          }))}
          showDetailOnBar
          color={EXPENSE.color}
          detailHeader="Pay"
          csvName={`Finans_gider_kategorileri_${range}`}
        />
        <RankedBars
          title="Hizmet bazında gelir"
          empty="Bu aralıkta ödenmiş fatura yok."
          rows={report.revenue_by_service.map((r) => ({ name: r.name, amount: r.amount, detail: `${r.count} fatura` }))}
          color={SOURCES[0].color}
          detailHeader="Fatura"
          csvName={`Finans_hizmet_geliri_${range}`}
        />
        <RankedBars
          title="Ürün bazında gelir"
          empty="Bu aralıkta ürün satışı yok."
          rows={report.revenue_by_product.map((r) => ({ name: r.name, amount: r.amount, detail: `${r.quantity} adet` }))}
          color={SOURCES[1].color}
          detailHeader="Adet"
          csvName={`Finans_urun_geliri_${range}`}
        />
      </div>
    </>
  );
}

// ---------------------------------------------------------------- comparison

function ComparisonCards({ report }: { report: Report }) {
  const { totals, previous } = report;
  const prevRange = `${format(fromISODate(previous.start_date), "d MMM", { locale: tr })} – ${format(
    fromISODate(previous.end_date), "d MMM yyyy", { locale: tr })}`;
  const items = [
    { label: "Toplam gelir", now: totals.income, before: previous.income, upIsGood: true },
    { label: "Toplam gider", now: totals.expense, before: previous.expense, upIsGood: false },
    { label: "Net kâr", now: totals.net, before: previous.net, upIsGood: true },
  ];
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="space-y-1 p-4">
            <p className="text-xs text-ink-muted">{item.label}</p>
            <p className="text-xl font-semibold tabular-nums text-ink">{formatCurrency(item.now)}</p>
            <Change now={item.now} before={item.before} upIsGood={item.upIsGood} />
            <p className="text-xs text-ink-muted">
              Önceki dönem ({prevRange}): <span className="tabular-nums">{formatCurrency(item.before)}</span>
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** Değişim: renk + ok + işaretli yüzde metni (renk tek başına bilgi taşımaz). */
function Change({ now, before, upIsGood }: { now: number; before: number; upIsGood: boolean }) {
  if (before === 0) {
    return <p className="text-xs text-ink-muted">{now === 0 ? "Değişim yok" : "Önceki dönemde kayıt yok"}</p>;
  }
  const pct = ((now - before) / Math.abs(before)) * 100;
  if (Math.abs(pct) < 0.05) {
    return <p className="flex items-center gap-1 text-xs text-ink-muted"><Minus className="h-3 w-3" aria-hidden /> Değişim yok</p>;
  }
  const up = pct > 0;
  const good = up === upIsGood;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  const text = `${up ? "+" : "−"}%${Math.abs(pct).toLocaleString("tr-TR", { maximumFractionDigits: 1 })}`;
  return (
    <p className={`flex items-center gap-1 text-xs font-medium ${good ? "text-success" : "text-danger"}`}>
      <Icon className="h-3 w-3" aria-hidden />
      {text} <span className="font-normal text-ink-muted">önceki döneme göre ({up ? "artış" : "azalış"})</span>
    </p>
  );
}

// ---------------------------------------------------------------- building blocks

function ChartCard({
  title, description, children, table, csv, note,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  table: ReactNode;
  csv: { name: string; headers: string[]; rows: string[][] };
  note?: ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-2 space-y-0">
        <div>
          <CardTitle className="text-base">{title}</CardTitle>
          {description && <p className="mt-1 text-xs text-ink-muted">{description}</p>}
        </div>
        <Button size="sm" variant="outline" className="gap-1" onClick={() => exportToCSV(csv.name, csv.headers, csv.rows)}>
          <Download className="h-4 w-4" aria-hidden /> CSV
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-[300px] sm:h-[360px]" role="img" aria-label={`${title} grafiği; sayılar aşağıdaki tabloda`}>
          {children}
        </div>
        {note && (
          <p className="flex gap-2 text-xs text-ink-muted"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />{note}</p>
        )}
        <details className="rounded-md border border-border">
          <summary className="cursor-pointer px-3 py-2 text-sm text-ink">Tablo olarak göster</summary>
          <div className="overflow-x-auto px-3 pb-3">{table}</div>
        </details>
      </CardContent>
    </Card>
  );
}

function TrendTable({ series, group }: { series: FinancePeriod[]; group: FinanceGroup }) {
  return (
    <table className="w-full min-w-[640px] text-sm">
      <caption className="sr-only">Dönem başına gelir kaynakları, gider ve net kâr</caption>
      <thead>
        <tr className="border-b border-border text-left text-xs text-ink-muted">
          <th scope="col" className="py-2 pr-3 font-medium">Dönem</th>
          {SOURCES.map((s) => <th key={s.key} scope="col" className="py-2 pr-3 text-right font-medium">{s.label}</th>)}
          <th scope="col" className="py-2 pr-3 text-right font-medium">Toplam gelir</th>
          <th scope="col" className="py-2 pr-3 text-right font-medium">Gider</th>
          <th scope="col" className="py-2 text-right font-medium">Net kâr</th>
        </tr>
      </thead>
      <tbody className="tabular-nums">
        {series.map((p) => (
          <tr key={p.period} className="border-b border-border/60 last:border-0">
            <th scope="row" className="py-1.5 pr-3 text-left font-normal text-ink">{periodLabel(p.period, group, true)}</th>
            {SOURCES.map((s) => <td key={s.key} className="py-1.5 pr-3 text-right text-ink-muted">{formatCurrency(p[s.key])}</td>)}
            <td className="py-1.5 pr-3 text-right text-ink">{formatCurrency(p.income)}</td>
            <td className="py-1.5 pr-3 text-right text-ink">{formatCurrency(p.expense)}</td>
            <td className="py-1.5 text-right font-medium text-ink">{formatCurrency(p.net)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Büyükten küçüğe yatay çubuklar; çubuğun ucunda tutar yazar (renksiz de okunur). */
function RankedBars({
  title, rows, color, empty, detailHeader, csvName, showDetailOnBar = false,
}: {
  title: string;
  rows: { name: string; amount: number; detail: string }[];
  color: string;
  empty: string;
  detailHeader: string;
  csvName: string;
  /** Çubuğun ucunda tutarın yanında detay da yazsın (ör. gider payı). */
  showDetailOnBar?: boolean;
}) {
  const height = Math.max(160, rows.length * 40 + 24);
  const data = rows.map((r) => ({ ...r, barLabel: showDetailOnBar && r.detail ? `${axisMoney(r.amount)} · ${r.detail}` : axisMoney(r.amount) }));
  return (
    <ChartCard
      title={title}
      csv={{ name: csvName, headers: ["Ad", "Tutar (TL)", detailHeader], rows: rows.map((r) => [r.name, csvNumber(r.amount), r.detail]) }}
      table={
        <table className="w-full text-sm">
          <caption className="sr-only">{title}</caption>
          <thead>
            <tr className="border-b border-border text-left text-xs text-ink-muted">
              <th scope="col" className="py-2 pr-3 font-medium">Ad</th>
              <th scope="col" className="py-2 pr-3 text-right font-medium">Tutar</th>
              <th scope="col" className="py-2 text-right font-medium">{detailHeader}</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {rows.map((r) => (
              <tr key={r.name} className="border-b border-border/60 last:border-0">
                <th scope="row" className="py-1.5 pr-3 text-left font-normal text-ink">{r.name}</th>
                <td className="py-1.5 pr-3 text-right text-ink">{formatCurrency(r.amount)}</td>
                <td className="py-1.5 text-right text-ink-muted">{r.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      {rows.length === 0 ? (
        <p className="flex h-full items-center justify-center text-sm text-ink-muted">{empty}</p>
      ) : (
        <div className="h-full overflow-y-auto">
          <div style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} layout="vertical" margin={{ top: 4, right: showDetailOnBar ? 104 : 72, left: 4, bottom: 4 }}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={110} tickLine={false} axisLine={false}
                       stroke="var(--ink-muted)" fontSize={12}
                       tickFormatter={(v: string) => (v.length > 16 ? `${v.slice(0, 15)}…` : v)} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--border)", opacity: 0.3 }}
                         formatter={(value: number) => [formatCurrency(value), "Tutar"]} />
                <Bar dataKey="amount" name="Tutar" fill={color} radius={[0, 4, 4, 0]} maxBarSize={24}>
                  <LabelList dataKey="barLabel" content={BarEndLabel} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </ChartCard>
  );
}

/** Çubuğun ucundaki etiket: tek satır (Recharts'ın varsayılanı dar ekranda metni satırlara böler). */
function BarEndLabel(props: { x?: number | string; y?: number | string; width?: number | string; height?: number | string; value?: number | string }) {
  const x = Number(props.x ?? 0) + Number(props.width ?? 0) + 6;
  const y = Number(props.y ?? 0) + Number(props.height ?? 0) / 2;
  return (
    <text x={x} y={y} dominantBaseline="central" fill="var(--ink)" fontSize={12}>
      {props.value}
    </text>
  );
}
