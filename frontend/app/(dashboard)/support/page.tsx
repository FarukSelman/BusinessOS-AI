"use client";

import { ChatWithHistory } from "@/components/chat/chat-with-history";

export default function SupportPage() {
  return (
    <ChatWithHistory
      title="Müşteri destek ajanı"
      description="İşletmenin bilgi tabanına dayanarak sorulara otomatik yanıt verir."
      agentColor="var(--agent-support)"
      examplePrompts={[
        "Çalışma saatleriniz nedir?",
        "İade politikanız nasıl işliyor?",
        "Fiyat listenizi görebilir miyim?",
      ]}
    />
  );
}