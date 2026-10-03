"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import { getActiveBusinessId } from "@/lib/business";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    if (!getActiveBusinessId()) {
      router.replace("/select-business");
      return;
    }
    setChecked(true);
  }, [router]);

  // Yönlendirme kararı verilene kadar hiçbir şey göstermiyoruz (flash önleme)
  if (!checked) return null;

  return <>{children}</>;
}
