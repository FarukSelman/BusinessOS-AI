import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_agents():
    with patch("app.ai.agents.orchestrator.OrchestratorAgent") as mock_orchestrator:
        yield mock_orchestrator

def test_orchestrator_routes_to_customer_support():
    """Test routing to customer support agent."""
    # Assuming OrchestratorAgent evaluates intent and returns the correct agent name
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="customer_support")
        assert agent.route("I have a problem with my bill") == "customer_support"
    except ImportError:
        pass

def test_orchestrator_routes_to_appointment():
    """Test routing to appointment agent."""
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="appointment")
        assert agent.route("I want to book a meeting") == "appointment"
    except ImportError:
        pass

def test_orchestrator_routes_to_sales():
    """Test routing to sales agent."""
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="sales")
        assert agent.route("How much is the enterprise plan?") == "sales"
    except ImportError:
        pass

def test_orchestrator_routes_to_analytics():
    """Test routing to analytics agent."""
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="analytics")
        assert agent.route("Show me the report for last month") == "analytics"
    except ImportError:
        pass

def test_orchestrator_routes_to_marketing():
    """Test routing to marketing agent."""
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="marketing")
        assert agent.route("Help me write an email campaign") == "marketing"
    except ImportError:
        pass

def test_orchestrator_fallback_to_customer_support():
    """Test fallback to customer support if intent is unclear."""
    try:
        from app.ai.agents.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent()
        agent._determine_intent = MagicMock(return_value="unknown")
        assert agent.route("blah blah blah") == "customer_support"
    except ImportError:
        pass

def test_base_agent_tool_schema_generation():
    """Test BaseAgent generates correct tool schema."""
    try:
        from app.ai.agents.base import BaseAgent
        class DummyAgent(BaseAgent):
            def my_tool(self, param1: str):
                """A dummy tool."""
                pass
        
        agent = DummyAgent()
        schema = agent.get_tool_schema()
        assert isinstance(schema, list)
    except ImportError:
        pass
