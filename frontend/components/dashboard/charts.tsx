"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import { format, subDays } from "date-fns";
import { tr } from "date-fns/locale";

const COLORS = {
  primary: "#6366f1",
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#06b6d4",
  purple: "#a855f7",
};

export function WeeklyAppointmentsChart({ appointments }: { appointments: any[] }) {
  const data = useMemo(() => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const d = subDays(new Date(), 6 - i);
      return {
        dateStr: format(d, 'yyyy-MM-dd'),
        display: format(d, 'EEE', { locale: tr }),
        count: 0
      };
    });

    appointments.forEach(app => {
      const day = last7Days.find(d => d.dateStr === app.appointment_date);
      if (day) day.count++;
    });

    return last7Days;
  }, [appointments]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
          <XAxis dataKey="display" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
            itemStyle={{ color: COLORS.primary }}
          />
          <Area type="monotone" dataKey="count" name="Randevular" stroke={COLORS.primary} fillOpacity={1} fill="url(#colorCount)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RevenueOverviewChart({ appointments, services }: { appointments: any[], services: any[] }) {
  const data = useMemo(() => {
    const revenueByService: Record<string, number> = {};
    
    const serviceMap = services.reduce((acc, s) => {
      acc[s.id] = { name: s.name, price: parseFloat(s.price) || 0 };
      return acc;
    }, {} as Record<string, { name: string, price: number }>);

    appointments.forEach(app => {
      if (app.status === "COMPLETED" && app.service_id && serviceMap[app.service_id]) {
        const sName = serviceMap[app.service_id].name;
        revenueByService[sName] = (revenueByService[sName] || 0) + serviceMap[app.service_id].price;
      }
    });

    return Object.entries(revenueByService)
      .map(([name, revenue]) => ({ name, revenue }))
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 5);
  }, [appointments, services]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
          <XAxis dataKey="name" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₺${val}`} />
          <Tooltip 
            formatter={(value: number) => [`₺${value}`, "Gelir"]}
            contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
            cursor={{ fill: 'var(--border)', opacity: 0.4 }}
          />
          <Bar dataKey="revenue" fill={COLORS.success} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function StatusDistributionChart({ appointments }: { appointments: any[] }) {
  const data = useMemo(() => {
    const counts = appointments.reduce((acc, app) => {
      acc[app.status] = (acc[app.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return [
      { name: 'Bekliyor', value: counts['PENDING'] || 0, color: COLORS.warning },
      { name: 'Onaylandı', value: counts['CONFIRMED'] || 0, color: COLORS.info },
      { name: 'Tamamlandı', value: counts['COMPLETED'] || 0, color: COLORS.success },
      { name: 'İptal', value: counts['CANCELLED'] || 0, color: COLORS.danger },
    ].filter(d => d.value > 0);
  }, [appointments]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
            itemStyle={{ color: 'var(--ink)' }}
          />
          <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--ink)' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ServicePopularityChart({ appointments, services }: { appointments: any[], services: any[] }) {
  const data = useMemo(() => {
    const counts: Record<string, number> = {};
    const serviceMap = services.reduce((acc, s) => {
      acc[s.id] = s.name;
      return acc;
    }, {} as Record<string, string>);

    appointments.forEach(app => {
      if (app.service_id && serviceMap[app.service_id]) {
        const sName = serviceMap[app.service_id];
        counts[sName] = (counts[sName] || 0) + 1;
      }
    });

    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [appointments, services]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart layout="vertical" data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" opacity={0.5} />
          <XAxis type="number" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="name" stroke="var(--ink-muted)" fontSize={12} tickLine={false} axisLine={false} width={80} />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--surface-elevated)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--ink)' }}
            cursor={{ fill: 'var(--border)', opacity: 0.4 }}
          />
          <Bar dataKey="count" name="Randevu Sayısı" fill={COLORS.purple} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
