"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessagesSquare,
  CalendarClock,
  ShoppingBag,
  LineChart,
  Megaphone,
  Users,
  FileText,
  UserCog,
  Receipt,
  Clock,
  Bell,
  Coins,
  ClipboardList,
  Star,
  Wallet,
  Banknote,
  Building2,
  ChevronDown,
  Bot,
  Briefcase,
  Settings2,
  BarChart3,
  Package,
  ShoppingCart,
  Gift,
  CreditCard,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: any;
  color: string;
}

interface NavGroup {
  label: string;
  icon: any;
  color: string;
  defaultOpen?: boolean;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "Genel",
    icon: LayoutDashboard,
    color: "var(--accent)",
    defaultOpen: true,
    items: [
      { href: "/dashboard", label: "Genel Bakış", icon: LayoutDashboard, color: "var(--accent)" },
      { href: "/customers", label: "Müşteriler", icon: Users, color: "var(--accent)" },
      { href: "/documents", label: "Bilgi Tabanı", icon: FileText, color: "var(--accent)" },
      { href: "/team", label: "Ekip", icon: UserCog, color: "var(--accent)" },
      { href: "/reports", label: "Raporlar", icon: BarChart3, color: "var(--accent)" },
    ],
  },
  {
    label: "İşletme",
    icon: Briefcase,
    color: "var(--accent)",
    defaultOpen: false,
    items: [
      { href: "/branches", label: "Şubeler", icon: Building2, color: "var(--accent)" },
      { href: "/staff", label: "Çalışanlar", icon: UserCog, color: "var(--accent)" },
      { href: "/schedule-settings", label: "Çalışma Saatleri", icon: Clock, color: "var(--agent-appointments)" },
      { href: "/reminder-settings", label: "Hatırlatmalar", icon: Bell, color: "var(--agent-appointments)" },
    ],
  },
  {
    label: "Ajanlar",
    icon: Bot,
    color: "var(--agent-support)",
    defaultOpen: false,
    items: [
      { href: "/support", label: "Müşteri Destek", icon: MessagesSquare, color: "var(--agent-support)" },
      { href: "/appointments", label: "Randevu Yönetimi", icon: CalendarClock, color: "var(--agent-appointments)" },
      { href: "/sales", label: "Satış & Öneri", icon: ShoppingBag, color: "var(--agent-sales)" },
      { href: "/marketing", label: "Pazarlama", icon: Megaphone, color: "var(--agent-marketing)" },
    ],
  },
  {
    label: "Finans",
    icon: LineChart,
    color: "var(--agent-finance)",
    defaultOpen: false,
    items: [
      { href: "/invoices", label: "Faturalar", icon: Receipt, color: "var(--agent-finance)" },
      { href: "/expenses", label: "Gelir-Gider", icon: Wallet, color: "var(--agent-finance)" },
      { href: "/cash-register", label: "Kasa Takibi", icon: Banknote, color: "var(--agent-finance)" },
      { href: "/finance", label: "Finansal Analiz", icon: LineChart, color: "var(--agent-finance)" },
    ],
  },
  {
    label: "Ürünler",
    icon: Package,
    color: "var(--agent-sales)",
    defaultOpen: false,
    items: [
      { href: "/products", label: "Stok Yönetimi", icon: Package, color: "var(--agent-sales)" },
      { href: "/product-sales", label: "Ürün Satışı", icon: ShoppingCart, color: "var(--agent-sales)" },
    ],
  },
  {
    label: "Paketler",
    icon: Gift,
    color: "var(--agent-appointments)",
    defaultOpen: false,
    items: [
      { href: "/packages", label: "Paket Hizmetler", icon: Gift, color: "var(--agent-appointments)" },
      { href: "/customer-packages", label: "Müşteri Paketleri", icon: Users, color: "var(--agent-appointments)" },
      { href: "/installments", label: "Taksit Takibi", icon: CreditCard, color: "var(--agent-appointments)" },
    ],
  },
  {
    label: "Müşteri İlişkileri",
    icon: Settings2,
    color: "var(--agent-sales)",
    defaultOpen: false,
    items: [
      { href: "/loyalty", label: "Parapuan", icon: Coins, color: "var(--agent-sales)" },
      { href: "/surveys", label: "Anketler", icon: ClipboardList, color: "var(--agent-marketing)" },
      { href: "/reviews", label: "Yorumlar", icon: Star, color: "var(--agent-sales)" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  // Auto-open the group that contains the active route
  const getInitialOpen = () => {
    const openState: Record<string, boolean> = {};
    navGroups.forEach((group) => {
      const hasActive = group.items.some((item) => pathname === item.href);
      openState[group.label] = hasActive || !!group.defaultOpen;
    });
    return openState;
  };

  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(getInitialOpen);

  const toggleGroup = (label: string) => {
    setOpenGroups((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  return (
    <aside className="flex h-screen w-64 flex-col bg-sidebar-bg">
      <div className="flex h-16 items-center border-b border-white/10 px-6">
        <span className="font-display text-lg font-semibold tracking-tight text-sidebar-ink">
          İşletme Paneli
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navGroups.map((group) => {
          const isOpen = openGroups[group.label] ?? false;
          const GroupIcon = group.icon;
          const hasActiveChild = group.items.some((item) => pathname === item.href);

          return (
            <div key={group.label}>
              {/* Group header */}
              <button
                onClick={() => toggleGroup(group.label)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-semibold transition-colors",
                  hasActiveChild
                    ? "text-sidebar-ink"
                    : "text-sidebar-muted hover:bg-white/5 hover:text-sidebar-ink"
                )}
              >
                <GroupIcon
                  className="h-4 w-4 shrink-0"
                  style={{ color: group.color }}
                />
                <span className="flex-1 text-left">{group.label}</span>
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 shrink-0 transition-transform duration-200",
                    isOpen && "rotate-180"
                  )}
                  style={{ opacity: 0.5 }}
                />
              </button>

              {/* Group items */}
              <div
                className={cn(
                  "overflow-hidden transition-all duration-200",
                  isOpen ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
                )}
              >
                <div className="ml-3 border-l border-white/5 pl-2 mt-1 space-y-0.5">
                  {group.items.map(({ href, label, icon: Icon, color }) => {
                    const active = pathname === href;
                    return (
                      <Link
                        key={href}
                        href={href}
                        style={
                          active
                            ? {
                                backgroundColor: `color-mix(in srgb, ${color} 18%, transparent)`,
                                borderColor: color,
                              }
                            : undefined
                        }
                        className={cn(
                          "flex items-center gap-3 rounded-md border-l-2 border-transparent px-3 py-1.5 text-[13px] font-medium transition-colors",
                          active
                            ? "text-sidebar-ink"
                            : "text-sidebar-muted hover:bg-white/5 hover:text-sidebar-ink"
                        )}
                      >
                        <Icon
                          className="h-3.5 w-3.5 shrink-0"
                          style={{ color }}
                        />
                        {label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
