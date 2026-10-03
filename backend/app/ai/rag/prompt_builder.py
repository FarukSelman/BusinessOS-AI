class PromptBuilder:
    """
    Builds the final prompt sent to the LLM.

    The SYSTEM_PROMPT is kept as a class constant
    so callers can pass it separately to the LLM provider
    as the system message — not embedded in the user text.
    """

    SYSTEM_PROMPT = """
Sen BusinessOS AI asistanısın.

Görevin:
Kullanıcının sorularını sadece sana verilen doküman içeriğine göre cevaplamaktır.

Kurallar:

1. Sadece CONTEXT bölümünde bulunan bilgileri kullan.
2. Kendi genel bilgini kullanma.
3. CONTEXT bölümünde cevap yoksa şu mesajı ver:
   "Bu bilgi yüklenen dokümanlarda bulunamadı."
4. Dokümanda olmayan bilgi üretme.
5. Tahmin yapma veya varsayımda bulunma.
6. Cevapları kısa, anlaşılır ve faydalı şekilde oluştur.
7. RAG, embedding veya teknik süreçlerden bahsetme.
8. Kullanıcıyla aynı dilde yanıt ver.
9. Konuşma geçmişi varsa, takip sorularını bağlamıyla birlikte değerlendir.
""".strip()


    def build(
        self,
        *,
        question: str,
        context: str,
        history=None,
    ) -> str:
        """
        Build the user prompt for the LLM.

        Returns only the user content (history + context + question).
        The system prompt should be passed separately via
        PromptBuilder.SYSTEM_PROMPT.
        """

        sections = []

        # --- Conversation History ---
        if history and hasattr(history, "messages") and history.messages:
            formatted_history = "\n".join(
                f"{msg.role}: {msg.content}"
                for msg in history.messages
            )
            sections.append(
                "--- CONVERSATION HISTORY ---\n"
                f"{formatted_history}"
            )

        # --- Context ---
        if context:
            sections.append(
                "--- CONTEXT ---\n"
                f"{context}"
            )
        else:
            sections.append(
                "--- CONTEXT ---\n"
                "Dokümanlardan ilgili bilgi bulunamadı."
            )

        # --- Question ---
        sections.append(
            "--- QUESTION ---\n"
            f"{question}"
        )

        return "\n\n".join(sections)