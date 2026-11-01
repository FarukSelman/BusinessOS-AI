"use client";

import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useState } from "react";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export const THEME_STORAGE_KEY = "theme";

/**
 * Temalı olmayan sayfalar: açılış, giriş/kayıt, işletme seçimi (giriş akışının
 * sabit koyu tasarımı) ve müşterilere açık online randevu sayfası kendi
 * tasarımlarını kullanır; <html class="dark"> onlara uygulanmaz.
 */
export const UNTHEMED_PATH = /^\/(?:$|login|register|select-business|book\/|auth\/)/;

/**
 * İlk boyamadan önce <head> içinde çalışır (app/layout.tsx): kayıtlı tercihi ya da
 * işletim sistemi tercihini okuyup <html>'e "dark" ekler. Böylece sayfa önce
 * aydınlık açılıp sonra kararmaz. React yüklenince ThemeScope aynı kararı devralır.
 */
export const themeInitScript = `(function(){try{
if(${UNTHEMED_PATH}.test(location.pathname))return;
var p=localStorage.getItem("${THEME_STORAGE_KEY}");
var d=p==="dark"||(p!=="light"&&matchMedia("(prefers-color-scheme: dark)").matches);
if(d)document.documentElement.classList.add("dark");
}catch(e){}})();`;

function readPreference(): ThemePreference {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

interface ThemeContextValue {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  setPreference: (p: ThemePreference) => void;
  /** Temalı bir sayfa (panel vb.) şu an ekranda mı. */
  scoped: boolean;
  setScoped: (v: boolean) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(() =>
    typeof window === "undefined" ? "system" : readPreference()
  );
  const [systemDark, setSystemDark] = useState(systemPrefersDark);
  // İlk değer yola göre: head script'iyle aynı kararı verip ilk karede sınıfı kaldırmayalım.
  const [scoped, setScoped] = useState(
    () => typeof window !== "undefined" && !UNTHEMED_PATH.test(window.location.pathname)
  );

  // "Sistem" seçiliyken işletim sistemi tema değiştirirse anında uy.
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setSystemDark(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  // Başka sekmede tercih değişirse bu sekmeye de yansıt.
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === THEME_STORAGE_KEY) setPreferenceState(readPreference());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const resolved: ResolvedTheme = preference === "dark" || (preference === "system" && systemDark) ? "dark" : "light";

  // Boyamadan önce uygula (useEffect bir kare geç kalıp yanıp sönmeye yol açar).
  useLayoutEffect(() => {
    document.documentElement.classList.toggle("dark", scoped && resolved === "dark");
  }, [scoped, resolved]);

  const setPreference = useCallback((p: ThemePreference) => {
    setPreferenceState(p);
    try {
      if (p === "system") window.localStorage.removeItem(THEME_STORAGE_KEY);
      else window.localStorage.setItem(THEME_STORAGE_KEY, p);
    } catch {
      // gizli pencere / kapalı depolama: tercih yalnızca bu oturumda geçerli
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ preference, resolved, setPreference, scoped, setScoped }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme, ThemeProvider içinde kullanılmalı");
  return ctx;
}

/** Temalı sayfaları sarar: ekrandayken karanlık tema uygulanabilir, çıkınca kaldırılır. */
export function ThemeScope({ children }: { children: React.ReactNode }) {
  const { setScoped } = useTheme();
  useLayoutEffect(() => {
    setScoped(true);
    return () => setScoped(false);
  }, [setScoped]);
  return <>{children}</>;
}
