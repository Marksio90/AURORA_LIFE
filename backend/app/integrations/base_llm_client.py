"""
Base LLM Client - Abstract base class for LLM integrations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import time

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM API clients.

    Provides common functionality for OpenAI, Claude, and other LLM providers.
    """

    def __init__(self, provider_name: str, api_key: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider_name: Name of the provider (e.g., "OpenAI", "Claude")
            api_key: Optional API key
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self._request_count = 0
        self._total_tokens = 0
        logger.info(f"{provider_name} client initialized")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion from message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Provider-specific parameters

        Returns:
            Completion response dict
        """
        pass

    def _log_request(self, tokens_used: int = 0):
        """Log API request for monitoring."""
        self._request_count += 1
        self._total_tokens += tokens_used
        logger.debug(
            f"{self.provider_name} request #{self._request_count}, "
            f"tokens: {tokens_used}, total: {self._total_tokens}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "provider": self.provider_name,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens
        }

    async def _handle_rate_limit(self, retry_count: int = 0, max_retries: int = 3):
        """
        Handle rate limiting with exponential backoff.

        Args:
            retry_count: Current retry attempt
            max_retries: Maximum number of retries
        """
        if retry_count >= max_retries:
            raise Exception(f"{self.provider_name} rate limit exceeded after {max_retries} retries")

        wait_time = (2 ** retry_count) * 1  # Exponential backoff: 1s, 2s, 4s
        logger.warning(f"{self.provider_name} rate limited. Waiting {wait_time}s (attempt {retry_count + 1}/{max_retries})")

        import asyncio
        await asyncio.sleep(wait_time)
