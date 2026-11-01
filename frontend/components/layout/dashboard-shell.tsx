"use client";

import { useState } from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";

/**
 * lg (1024px) ve üstünde sol menü sabit durur ve sayfayla kaymaz (sticky).
 * Daha dar ekranlarda menü gizlenir; navbar'daki butonla soldan açılan bir
 * çekmece (drawer) olarak gelir.
 */
export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <div className="sticky top-0 hidden h-screen shrink-0 lg:block">
        <Sidebar />
      </div>

      <DialogPrimitive.Root open={navOpen} onOpenChange={setNavOpen}>
        <DialogPrimitive.Portal>
          <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/40 lg:hidden" />
          <DialogPrimitive.Content
            className="fixed inset-y-0 left-0 z-50 flex shadow-xl outline-none lg:hidden"
            aria-describedby={undefined}
          >
            <DialogPrimitive.Title className="sr-only">Menü</DialogPrimitive.Title>
            <Sidebar onNavigate={() => setNavOpen(false)} />
            <DialogPrimitive.Close
              className="absolute right-2 top-4 rounded-md p-2 text-sidebar-muted hover:bg-white/5 hover:text-sidebar-ink"
              aria-label="Menüyü kapat"
            >
              <X className="h-5 w-5" />
            </DialogPrimitive.Close>
          </DialogPrimitive.Content>
        </DialogPrimitive.Portal>
      </DialogPrimitive.Root>

      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar onMenuClick={() => setNavOpen(true)} />
        <main className="min-w-0 flex-1 bg-surface p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
