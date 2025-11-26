"""
Claude API integration for advanced AI reasoning
"""
from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings


class ClaudeClient:
    """
    Claude API client for AURORA_LIFE.

    Features:
    - Advanced reasoning for complex life decisions
    - Long-form content analysis
    - Multi-turn conversations
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncAnthropic(
            api_key=api_key or getattr(settings, 'ANTHROPIC_API_KEY', None)
        )
        self.model = "claude-3-opus-20240229"

    async def create_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Create Claude message completion.

        Args:
            messages: List of message dicts
            system: Optional system prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Completion response
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=messages
        )

        return {
            "content": response.content[0].text if response.content else "",
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def analyze_life_decision(
        self,
        decision: str,
        context: Dict[str, Any],
        user_values: List[str]
    ) -> str:
        """
        Analyze complex life decision using Claude's reasoning.

        Args:
            decision: The decision to analyze
            context: User context and relevant data
            user_values: User's core values

        Returns:
            Detailed analysis and recommendations
        """
        system_prompt = """You are a thoughtful life advisor using Claude's advanced reasoning.
        Help users make better life decisions by considering their values, context, and long-term impact.
        Provide balanced, nuanced analysis."""

        user_prompt = f"""I need help with this decision: {decision}

My values: {', '.join(user_values)}

Context:
{context}

Please provide:
1. Analysis of pros and cons
2. Alignment with my values
3. Short-term and long-term implications
4. Alternative perspectives
5. Actionable recommendation"""

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        result = await self.create_message(
            messages=messages,
            system=system_prompt,
            max_tokens=2000
        )

        return result["content"]

    async def generate_weekly_reflection(
        self,
        week_data: Dict[str, Any]
    ) -> str:
        """
        Generate thoughtful weekly reflection from user's data.

        Args:
            week_data: User's weekly events, patterns, achievements

        Returns:
            Personalized weekly reflection
        """
        system_prompt = """You are a reflective life coach generating weekly reflections.
        Create meaningful, encouraging reflections that help users grow and improve."""

        user_prompt = f"""Generate a thoughtful weekly reflection based on this data:

{week_data}

Include:
- Key highlights and achievements
- Patterns observed
- Areas for improvement
- Encouragement and motivation
- Specific suggestions for next week"""

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        result = await self.create_message(messages, system=system_prompt)
        return result["content"]
