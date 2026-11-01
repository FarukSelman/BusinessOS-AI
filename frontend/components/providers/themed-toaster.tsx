"use client";

import { Toaster } from "sonner";
import { useTheme } from "@/lib/theme";

/** Bildirimler temalı sayfalarda temayı izler; diğer sayfalarda aydınlık kalır. */
export function ThemedToaster() {
  const { resolved, scoped } = useTheme();
  return <Toaster richColors position="top-right" theme={scoped ? resolved : "light"} />;
}
