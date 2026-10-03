from app.ai.llm.service import LLMService
from app.ai.memory.schemas import ConversationHistory


class QueryRewriter:
    """
    Converts follow-up questions into standalone questions.

    Uses a dedicated system prompt for query rewriting,
    separate from the RAG system prompt.
    """

    SYSTEM_PROMPT = """
Sen bir sorgu yeniden yazma asistanısın.

Görevin:
Kullanıcının son sorusunu, konuşma geçmişini kullanarak
bağımsız (standalone) bir soruya dönüştürmektir.

Kurallar:

1. "bu", "şu", "o", "bunun", "onun", "bunu" gibi
   gönderme zamirlerini açık ifadelerle değiştir.
2. Sorunun anlamını değiştirme.
3. Soruyu cevaplama, sadece yeniden yaz.
4. Sadece yeniden yazılmış soruyu döndür, başka bir şey ekleme.
5. Soruyla aynı dilde yaz.
""".strip()


    def __init__(
        self,
        llm_service: LLMService,
    ):
        self.llm_service = llm_service



    def rewrite(
        self,
        *,
        question: str,
        history: ConversationHistory,
    ) -> str:
        

        if not history or not history.messages:
            return question



        history_text = "\n".join(
            [
                f"{msg.role}: {msg.content}"
                for msg in history.messages
            ]
        )


        prompt = f"""Konuşma geçmişi:

{history_text}

Son soru:

{question}

Bağımsız soru:"""


        return self.llm_service.generate(
            prompt.strip(),
            system_prompt=self.SYSTEM_PROMPT,
        )