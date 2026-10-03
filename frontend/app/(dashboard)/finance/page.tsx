"use client";

import { ChatWithHistory } from "@/components/chat/chat-with-history";

export default function FinancePage() {
  return (
    <ChatWithHistory
      title="Finansal analiz"
      description="İşletme verilerine dayalı özet göstergeler ve analiz ajanıyla sohbet."
      agentColor="var(--agent-finance)"
      examplePrompts={[
        "Bu ay kaç randevu tamamlandı?",
        "En popüler hizmet hangisi?",
        "Müşteri sayım nasıl değişiyor?",
      ]}
    />
  );
}