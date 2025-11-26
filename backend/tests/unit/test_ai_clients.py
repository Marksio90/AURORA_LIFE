"""
Unit tests for AI clients (OpenAI and Claude) with BaseLLMClient.
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

    def test_initialization(self, openai_client):
        """Test client initialization from BaseLLMClient."""
        assert openai_client.provider_name == "OpenAI"
        assert openai_client.api_key == "test-key"
        assert openai_client._request_count == 0
        assert openai_client._total_tokens == 0
        assert openai_client.model == "gpt-4-turbo-preview"

    @pytest.mark.asyncio
    async def test_chat_completion(self, openai_client):
        """Test chat completion generation."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_response.choices[0].message.function_call = None
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 30
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

        # Verify usage logging from BaseLLMClient
        assert openai_client._request_count == 1
        assert openai_client._total_tokens == 30

    @pytest.mark.asyncio
    async def test_generate(self, openai_client):
        """Test simple generate method."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_response.choices[0].message.function_call = None
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 15
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15
        }

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        result = await openai_client.generate("Test prompt")

        assert result == "Generated response"
        assert openai_client._request_count == 1
        assert openai_client._total_tokens == 15

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, openai_client):
        """Test generate with system prompt."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "System-guided response"
        mock_response.choices[0].message.function_call = None
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 25
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }

        openai_client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Test
        result = await openai_client.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant."
        )

        assert result == "System-guided response"

    def test_get_stats(self, openai_client):
        """Test get_stats from BaseLLMClient."""
        # Simulate some requests
        openai_client._request_count = 5
        openai_client._total_tokens = 150

        stats = openai_client.get_stats()

        assert stats["provider"] == "OpenAI"
        assert stats["request_count"] == 5
        assert stats["total_tokens"] == 150


class TestClaudeClient:
    """Tests for Claude client."""

    @pytest.fixture
    def claude_client(self):
        """Create Claude client instance."""
        with patch('app.integrations.claude_client.AsyncAnthropic'):
            return ClaudeClient(api_key="test-key")

    def test_initialization(self, claude_client):
        """Test client initialization from BaseLLMClient."""
        assert claude_client.provider_name == "Claude"
        assert claude_client.api_key == "test-key"
        assert claude_client._request_count == 0
        assert claude_client._total_tokens == 0
        assert claude_client.model == "claude-3-opus-20240229"

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

        # Verify usage logging from BaseLLMClient
        assert claude_client._request_count == 1
        assert claude_client._total_tokens == 30  # 10 + 20

    @pytest.mark.asyncio
    async def test_chat_completion(self, claude_client):
        """Test chat_completion wrapper method."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Chat response")]
        mock_response.usage = Mock(input_tokens=15, output_tokens=25)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        messages = [{"role": "user", "content": "Hello"}]
        result = await claude_client.chat_completion(messages, max_tokens=1024, temperature=0.7)

        assert result["content"] == "Chat response"
        assert result["usage"]["input_tokens"] == 15
        assert result["usage"]["output_tokens"] == 25

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
        assert claude_client._request_count == 1
        assert claude_client._total_tokens == 300  # 100 + 200

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
        """Test simple generate method with system_prompt support."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        claude_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Test
        result = await claude_client.generate("Test prompt", system_prompt="You are helpful.")

        assert result == "Generated response"
        assert claude_client._request_count == 1
        assert claude_client._total_tokens == 30

    def test_get_stats(self, claude_client):
        """Test get_stats from BaseLLMClient."""
        # Simulate some requests
        claude_client._request_count = 3
        claude_client._total_tokens = 90

        stats = claude_client.get_stats()

        assert stats["provider"] == "Claude"
        assert stats["request_count"] == 3
        assert stats["total_tokens"] == 90


class TestBaseLLMClientIntegration:
    """Test that both clients properly inherit from BaseLLMClient."""

    @pytest.fixture
    def openai_client(self):
        with patch('app.integrations.openai_client.AsyncOpenAI'):
            return OpenAIClient(api_key="test-key")

    @pytest.fixture
    def claude_client(self):
        with patch('app.integrations.claude_client.AsyncAnthropic'):
            return ClaudeClient(api_key="test-key")

    def test_both_have_common_interface(self, openai_client, claude_client):
        """Test that both clients share common BaseLLMClient interface."""
        # Both should have these methods from BaseLLMClient
        assert hasattr(openai_client, 'get_stats')
        assert hasattr(claude_client, 'get_stats')
        assert hasattr(openai_client, '_log_request')
        assert hasattr(claude_client, '_log_request')
        assert hasattr(openai_client, 'generate')
        assert hasattr(claude_client, 'generate')
        assert hasattr(openai_client, 'chat_completion')
        assert hasattr(claude_client, 'chat_completion')

    def test_log_request_tracking(self, openai_client):
        """Test _log_request method from BaseLLMClient."""
        assert openai_client._request_count == 0
        assert openai_client._total_tokens == 0

        openai_client._log_request(50)
        assert openai_client._request_count == 1
        assert openai_client._total_tokens == 50

        openai_client._log_request(30)
        assert openai_client._request_count == 2
        assert openai_client._total_tokens == 80
