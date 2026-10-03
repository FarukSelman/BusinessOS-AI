"use client";

import { ChatWithHistory } from "@/components/chat/chat-with-history";

export default function SalesPage() {
  return (
    <ChatWithHistory
      title="Satış ve öneri ajanı"
      description="Ürün/hizmet kataloğunu yönet — ajan müşterilere buradan öneri sunar."
      agentColor="var(--agent-sales)"
      examplePrompts={[
        "Elimde ne var, hangisini önerirsin?",
        "En uygun paket hangisi?",
        "Fiyatları karşılaştır",
      ]}
    />
  );
}