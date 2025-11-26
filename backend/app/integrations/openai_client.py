"""
OpenAI API integration for natural language processing
"""
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings


class OpenAIClient:
    """
    OpenAI API client for AURORA_LIFE.

    Features:
    - Chat completions for conversational AI
    - Embeddings for semantic search
    - Function calling for tool use
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or getattr(settings, 'OPENAI_API_KEY', None)
        )
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

        return {
            "content": response.choices[0].message.content,
            "function_call": response.choices[0].message.function_call if functions else None,
            "usage": response.usage.model_dump() if response.usage else None
        }

    async def generate_insights(
        self,
        user_data: Dict[str, Any],
        context: str = "general"
    ) -> str:
        """
        Generate personalized insights from user data.

        Args:
            user_data: User's life data (events, metrics, patterns)
            context: Context for insights (health, productivity, mood, etc.)

        Returns:
            Generated insights text
        """
        system_prompt = """You are an AI life coach for AURORA_LIFE platform.
        Analyze user data and provide personalized, actionable insights.
        Be empathetic, specific, and evidence-based."""

        user_prompt = f"""Analyze this user's data and provide insights for {context}:

User Data:
{user_data}

Provide 3-5 key insights with actionable recommendations."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        result = await self.chat_completion(messages, temperature=0.7)
        return result["content"]

    async def analyze_mood_from_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze mood/emotions from text using GPT-4.

        Args:
            text: User's text input

        Returns:
            Mood analysis with sentiment, emotions, and score
        """
        system_prompt = """Analyze the mood and emotions in the provided text.
        Return a JSON object with: sentiment (positive/negative/neutral),
        emotions (list), mood_score (0-1), and brief analysis."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        result = await self.chat_completion(messages, temperature=0.3, max_tokens=300)

        # Parse JSON response
        import json
        try:
            return json.loads(result["content"])
        except:
            return {
                "sentiment": "neutral",
                "emotions": [],
                "mood_score": 0.5,
                "analysis": result["content"]
            }

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for semantic search.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        return [item.embedding for item in response.data]

    async def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Simple text generation method.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        result = await self.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
        return result["content"] or ""
