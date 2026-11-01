"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme, type ThemePreference } from "@/lib/theme";
import { cn } from "@/lib/utils";

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Açık", icon: Sun },
  { value: "dark", label: "Koyu", icon: Moon },
  { value: "system", label: "Sistem", icon: Monitor },
];

/** Navbar'daki tema düğmesi: ikon seçili tercihi gösterir, menüden Açık/Koyu/Sistem seçilir. */
export function ThemeToggle() {
  const { preference, setPreference } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = OPTIONS.find((o) => o.value === preference) ?? OPTIONS[2];
  const Icon = current.icon;

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Tema: ${current.label}`}
        title={`Tema: ${current.label}`}
      >
        <Icon className="h-5 w-5 text-ink-muted" />
      </Button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-36 overflow-hidden rounded-lg border border-border bg-surface-elevated py-1 shadow-lg"
        >
          {OPTIONS.map(({ value, label, icon: OptionIcon }) => (
            <button
              key={value}
              type="button"
              role="menuitemradio"
              aria-checked={preference === value}
              onClick={() => {
                setPreference(value);
                setOpen(false);
              }}
              className={cn(
                "flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-ink hover:bg-surface",
                preference === value && "font-medium"
              )}
            >
              <OptionIcon className="h-4 w-4 text-ink-muted" />
              <span className="flex-1">{label}</span>
              {preference === value && <Check className="h-4 w-4 text-accent-text" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
