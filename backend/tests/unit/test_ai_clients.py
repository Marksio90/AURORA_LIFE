"""
Unit tests for AI clients (OpenAI and Claude).
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.openai_client import OpenAIClient
from app.integrations.claude_client import ClaudeClient


class TestOpenAIClient:
    """Tests for OpenAI client."""

    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client instance."""
        with patch('app.integrations.openai_client.AsyncOpenAI'):
            return OpenAIClient(api_key="test-key")

    @pytest.mark.asyncio
    async def test_chat_completion(self, openai_client):
        """Test chat completion generation."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_response.choices[0].message.function_call = None
        mock_response.usage = Mock()
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        messages = [{"role": "user", "content": "Hello"}]
        result = await openai_client.chat_completion(messages)

        assert result["content"] == "Hello! How can I help you?"
        assert result["usage"]["total_tokens"] == 30
        assert result["function_call"] is None

    @pytest.mark.asyncio
    async def test_generate_insights(self, openai_client):
        """Test insight generation."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Based on your data, you should sleep more."
        mock_response.choices[0].message.function_call = None
        mock_response.usage = None

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        user_data = {"sleep_hours": 5.5, "energy_level": 3}
        result = await openai_client.generate_insights(user_data, "health")

        assert "sleep" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_mood_from_text(self, openai_client):
        """Test mood analysis from text."""
        # Mock response with JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{"sentiment": "positive", "emotions": ["happy", "excited"], "mood_score": 0.8, "analysis": "Very positive"}'''
        mock_response.choices[0].message.function_call = None
        mock_response.usage = None

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        result = await openai_client.analyze_mood_from_text("I'm feeling great today!")

        assert result["sentiment"] == "positive"
        assert "happy" in result["emotions"]
        assert result["mood_score"] == 0.8

    @pytest.mark.asyncio
    async def test_create_embeddings(self, openai_client):
        """Test embedding creation."""
        # Mock response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]

        openai_client.client.embeddings.create = AsyncMock(return_value=mock_response)

        # Test
        texts = ["Hello world", "Test text"]
        result = await openai_client.create_embeddings(texts)

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_generate(self, openai_client):
        """Test simple generate method."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_response.choices[0].message.function_call = None
        mock_response.usage = None

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        result = await openai_client.generate("Test prompt")

        assert result == "Generated response"


class TestClaudeClient:
    """Tests for Claude client."""

    @pytest.fixture
    def claude_client(self):
        """Create Claude client instance."""
        with patch('app.integrations.claude_client.AsyncAnthropic'):
            return ClaudeClient(api_key="test-key")

    @pytest.mark.asyncio
    async def test_create_message(self, claude_client):
        """Test message creation."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude's response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        messages = [{"role": "user", "content": "Hello"}]
        result = await claude_client.create_message(messages)

        assert result["content"] == "Claude's response"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 20

    @pytest.mark.asyncio
    async def test_analyze_life_decision(self, claude_client):
        """Test life decision analysis."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Detailed analysis of your decision...")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        decision = "Should I change careers?"
        context = {"current_job": "Developer", "years_experience": 5}
        values = ["growth", "impact", "balance"]

        result = await claude_client.analyze_life_decision(decision, context, values)

        assert "analysis" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_weekly_reflection(self, claude_client):
        """Test weekly reflection generation."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="This week you achieved great things...")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=100)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        week_data = {
            "achievements": ["Completed project", "Exercised 5 days"],
            "challenges": ["Low energy on Tuesday"]
        }

        result = await claude_client.generate_weekly_reflection(week_data)

        assert "week" in result.lower() or "achieved" in result.lower()

    @pytest.mark.asyncio
    async def test_generate(self, claude_client):
        """Test simple generate method."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        result = await claude_client.generate("Test prompt")

        assert result == "Generated response"
