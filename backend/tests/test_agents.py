import json
import uuid
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock

from app.ai.agents.schemas import AgentContext, AgentResponse


# ---------------------------------------------------------------- routing
# The LLM classifier is mocked (client.chat returns the intent) and every
# specialist's execute() is replaced, so a test sees which agent got the question.

def _routed(client, role="OWNER"):
    orchestrator = _orchestrator(client)
    for name, agent in orchestrator.agents.items():
        agent.execute = MagicMock(return_value=AgentResponse(answer=f"{name} yanıtı", agent_name=name))
    context = AgentContext(business_id=uuid.uuid4(), user_id=uuid.uuid4(), business_name="Kuaför", role=role)
    return orchestrator, context


@pytest.mark.parametrize("intent, question", [
    ("customer_support", "Faturamla ilgili bir sorunum var"),
    ("appointment", "Yarın için randevu almak istiyorum"),
    ("sales", "Kurumsal paketin fiyatı ne kadar?"),
    ("analytics", "Geçen ayın raporunu göster"),
    ("marketing", "Bir e-posta kampanyası yazmama yardım et"),
    ("finance", "Bu ay ne kadar gelir elde ettik?"),
])
def test_orchestrator_routes_to_the_classified_agent(intent, question):
    client = MagicMock()
    client.chat.return_value = intent
    orchestrator, context = _routed(client)

    response = orchestrator.route(question=question, context=context)

    assert response.agent_name == intent
    orchestrator.agents[intent].execute.assert_called_once()
    assert orchestrator.agents[intent].execute.call_args.kwargs["question"] == question
    others = [a for name, a in orchestrator.agents.items() if name != intent]
    assert not any(a.execute.called for a in others)


def test_orchestrator_reads_the_agent_name_out_of_a_wordy_answer():
    client = MagicMock()
    client.chat.return_value = "Ajan: marketing."
    orchestrator, context = _routed(client)
    assert orchestrator.route(question="Kampanya hazırla", context=context).agent_name == "marketing"


def test_orchestrator_fallback_to_customer_support():
    """An answer that names no agent goes to customer support."""
    client = MagicMock()
    client.chat.return_value = "bilmiyorum"
    orchestrator, context = _routed(client)
    response = orchestrator.route(question="blah blah blah", context=context)
    assert response.agent_name == "customer_support"
    orchestrator.agents["customer_support"].execute.assert_called_once()


@pytest.mark.parametrize("role", ["EMPLOYEE", "VIEWER"])
def test_orchestrator_keeps_finance_from_non_finance_roles(role):
    client = MagicMock()
    client.chat.return_value = "finance"
    orchestrator, context = _routed(client, role=role)
    response = orchestrator.route(question="Bu ay ne kadar kâr ettik?", context=context)
    assert response.metadata == {"access_denied": True}
    assert not orchestrator.agents["finance"].execute.called


# ---------------------------------------------------------------- base agent

def _dummy_agent(client):
    from app.ai.agents.base import BaseAgent
    from app.ai.agents.tools.base import BaseTool, ToolResult

    class EchoTool(BaseTool):
        name = "echo"
        description = "Verilen metni geri döndürür."
        parameters = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

        def execute(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, output=f"echo: {kwargs['text']}")

    class DummyAgent(BaseAgent):
        name = "dummy"
        description = "Test ajanı"
        system_prompt = "Sen bir test ajanısın."
        tools = [EchoTool()]

    return DummyAgent(client)


def _llm_reply(content=None, tool_calls=None):
    return SimpleNamespace(
        content=content, tool_calls=tool_calls,
        model_dump=lambda: {"role": "assistant", "content": content},
    )


def test_base_agent_tool_schema_generation():
    """Every tool reaches the LLM in OpenAI function-calling format."""
    client = MagicMock()
    client.chat_with_tools.return_value = _llm_reply(content="tamam")
    agent = _dummy_agent(client)

    context = AgentContext(business_id=uuid.uuid4(), user_id=uuid.uuid4(), business_name="Kuaför")
    response = agent.execute(question="merhaba", context=context)

    assert response.answer == "tamam" and response.agent_name == "dummy"
    schemas = client.chat_with_tools.call_args.kwargs["tools"]
    assert schemas == [{
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Verilen metni geri döndürür.",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        },
    }]


def test_base_agent_runs_the_tool_the_llm_asks_for():
    call = SimpleNamespace(id="call-1", function=SimpleNamespace(name="echo", arguments=json.dumps({"text": "selam"})))
    client = MagicMock()
    client.chat_with_tools.side_effect = [_llm_reply(tool_calls=[call]), _llm_reply(content="bitti")]
    agent = _dummy_agent(client)

    context = AgentContext(business_id=uuid.uuid4(), user_id=uuid.uuid4(), business_name="Kuaför")
    response = agent.execute(question="selam de", context=context)

    assert response.answer == "bitti" and response.tools_used == ["echo"]
    second_messages = client.chat_with_tools.call_args_list[1].kwargs["messages"]
    assert second_messages[-1] == {"role": "tool", "tool_call_id": "call-1", "content": "echo: selam"}


def test_current_date_note_uses_app_timezone():
    from datetime import UTC, datetime
    from zoneinfo import ZoneInfo

    from app.ai.agents.base import current_date_note

    now = datetime(2026, 10, 4, 22, 30, tzinfo=UTC).astimezone(ZoneInfo("Europe/Istanbul"))
    note = current_date_note(now)
    assert "5 Ekim 2026 Pazartesi (2026-10-05)" in note
    assert "saat 01:30" in note


def test_every_agent_system_message_contains_today():
    import uuid
    from unittest import mock

    from app.ai.agents.orchestrator import AgentOrchestrator
    from app.ai.agents.schemas import AgentContext

    orchestrator = AgentOrchestrator(
        client=mock.MagicMock(), db=mock.MagicMock(), business_id=uuid.uuid4(),
        user_id=uuid.uuid4(), embedding_service=mock.MagicMock(), role="OWNER",
    )
    context = AgentContext(business_id=uuid.uuid4(), user_id=uuid.uuid4(), business_name="Kuaför")
    for agent in orchestrator.agents.values():
        system = agent._build_messages(question="yarın boş saat var mı?", context=context)[0]["content"]
        assert "Bugünün tarihi:" in system, agent.name
        assert "Kuaför" in system


def _orchestrator(client):
    import uuid
    from unittest import mock

    from app.ai.agents.orchestrator import AgentOrchestrator

    return AgentOrchestrator(
        client=client, db=mock.MagicMock(), business_id=uuid.uuid4(),
        user_id=uuid.uuid4(), embedding_service=mock.MagicMock(), role="OWNER",
    )


@pytest.mark.parametrize("question, expected", [
    ("Bu ay ne kadar gelir elde ettik?", "finance"),
    ("Bugün 500 TL elektrik faturası ödedim, gider olarak kaydet.", "finance"),
    ("Yarın saat 15:00'e Ayşe Kaya için randevu oluştur.", "appointment"),
    ("Mehmet'in randevusunu İPTAL et", "appointment"),
    ("Son 30 günde kaç randevumuz oldu?", "analytics"),
    ("%15 indirimli kampanya hazırla", "marketing"),
    ("Stoğu azalan ürünler hangileri?", "sales"),
    ("Çalışma saatleriniz nedir?", "customer_support"),
])
def test_classifier_outage_falls_back_to_keywords(question, expected):
    client = MagicMock()
    client.chat.side_effect = ConnectionError("Connection error.")
    assert _orchestrator(client)._classify_intent(question=question) == expected


def test_classifier_answer_still_wins_when_available():
    client = MagicMock()
    client.chat.return_value = "sales"
    assert _orchestrator(client)._classify_intent(question="Bu ay ne kadar gelir elde ettik?") == "sales"


def test_system_message_asks_for_the_users_language():
    import uuid

    from app.ai.agents.schemas import AgentContext

    context = AgentContext(business_id=uuid.uuid4(), user_id=uuid.uuid4(), business_name="Kuaför")
    for agent in _orchestrator(MagicMock()).agents.values():
        system = agent._build_messages(question="What are your opening hours?", context=context)[0]["content"]
        assert "İngilizce soruya İngilizce" in system, agent.name


def test_openai_client_retries_transient_errors(monkeypatch):
    from app.ai.openai.client import OpenAIClient
    from app.core.config import settings

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key-not-used")
    client = OpenAIClient()
    assert client.client.max_retries >= 3
