"""
OpenAI API integration for natural language processing
"""
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.integrations.base_llm_client import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """
    OpenAI API client for AURORA_LIFE.

    Features:
    - Chat completions for conversational AI
    - Embeddings for semantic search
    - Function calling for tool use
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            provider_name="OpenAI",
            api_key=api_key or getattr(settings, 'OPENAI_API_KEY', None)
        )
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo-preview"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            functions: Optional function definitions for function calling
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Returns:
            Completion response
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if functions:
            kwargs["functions"] = functions
            kwargs["function_call"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)

        # Log usage
        if response.usage:
            self._log_request(response.usage.total_tokens)

        return {
            "content": response.choices[0].message.content,
            "function_call": response.choices[0].message.function_call if functions else None,
            "usage": response.usage.model_dump() if response.usage else None
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Simple text generation method.

        Args:
            prompt: Input prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = await self.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
        return result["content"] or ""
