"use client";

import { ChatWithHistory } from "@/components/chat/chat-with-history";
import { FinanceOnly } from "@/components/layout/finance-only";

// Yalnızca sahip/yönetici; finans ajanı da bu rollerle sınırlı (orkestratör).
export default function FinancePage() {
  return (
    <FinanceOnly>
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
    </FinanceOnly>
  );
}
