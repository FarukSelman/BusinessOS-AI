"use client";

import { ChatWithHistory } from "@/components/chat/chat-with-history";

export default function MarketingPage() {
  return (
    <ChatWithHistory
      title="Pazarlama ve kampanya öneri ajanı"
      description="Gerçek hizmet ve müşteri verilerine dayanarak kampanya fikirleri üretir."
      agentColor="var(--agent-marketing)"
      examplePrompts={[
        "En az tercih edilen hizmetimiz için bir kampanya öner",
        "Yeni müşteri kazanmak için bir fikir ver",
        "Bu hafta için kısa bir sosyal medya gönderisi yaz",
        "Son 60 gündür gelmeyen müşteriler için boş saatleri dolduracak kampanya taslağı oluştur",
      ]}
    />
  );
}
