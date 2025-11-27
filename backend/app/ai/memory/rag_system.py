"""
RAG (Retrieval Augmented Generation) System for AI Agents

Combines:
- Vector store retrieval (semantic search)
- LLM generation (context-aware responses)
- Agent memory (long-term context)

Enables agents to:
- Remember past conversations
- Reference historical user data
- Provide context-aware recommendations
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.ai.memory.vector_store import VectorStore, MemoryManager
from app.integrations.openai_client import get_openai_client
from app.integrations.anthropic_client import get_anthropic_client


class RAGSystem:
    """
    Retrieval Augmented Generation system.

    Workflow:
    1. User query → Retrieve relevant context from vector store
    2. Context + Query → Generate response with LLM
    3. Store interaction in memory for future context
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_provider: str = "openai",
        model_name: str = "gpt-4"
    ):
        """
        Initialize RAG system.

        Args:
            vector_store: Vector store for retrieval
            llm_provider: 'openai' or 'anthropic'
            model_name: Model to use
        """
        self.vector_store = vector_store
        self.memory_manager = MemoryManager(vector_store)

        self.llm_provider = llm_provider
        self.model_name = model_name

        # LLM clients
        self.openai_client = None
        self.anthropic_client = None

        if llm_provider == "openai":
            self.openai_client = get_openai_client()
        elif llm_provider == "anthropic":
            self.anthropic_client = get_anthropic_client()

    async def query(
        self,
        user_id: int,
        question: str,
        context_window: int = 5,
        include_memory_types: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.

        Args:
            user_id: User ID
            question: User's question
            context_window: Number of relevant memories to retrieve
            include_memory_types: Filter by memory types
            system_prompt: Optional system prompt override

        Returns:
            Answer with sources and metadata
        """
        # 1. Retrieve relevant context
        retrieved_memories = []

        if include_memory_types:
            for mem_type in include_memory_types:
                memories = self.memory_manager.recall(
                    user_id=user_id,
                    query=question,
                    memory_type=mem_type,
                    top_k=context_window
                )
                retrieved_memories.extend(memories)
        else:
            retrieved_memories = self.memory_manager.recall(
                user_id=user_id,
                query=question,
                top_k=context_window
            )

        # Sort by relevance
        retrieved_memories.sort(key=lambda m: m['score'], reverse=True)
        retrieved_memories = retrieved_memories[:context_window]

        # 2. Build context
        context = self._build_context(retrieved_memories)

        # 3. Generate response
        if system_prompt is None:
            system_prompt = self._default_system_prompt()

        response = await self._generate_response(
            question=question,
            context=context,
            system_prompt=system_prompt
        )

        # 4. Store this interaction in memory
        interaction_text = f"User asked: {question}\nAssistant answered: {response}"
        self.memory_manager.add_episodic_memory(
            user_id=user_id,
            event_text=interaction_text,
            event_type='conversation',
            timestamp=datetime.now()
        )

        return {
            'answer': response,
            'sources': [
                {
                    'text': m['text'],
                    'metadata': m['metadata'],
                    'relevance_score': m['score']
                }
                for m in retrieved_memories
            ],
            'context_used': len(retrieved_memories) > 0,
            'timestamp': datetime.now().isoformat()
        }

    def _build_context(self, memories: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved memories."""
        if not memories:
            return "No relevant historical context found."

        context_parts = ["Relevant historical context:"]

        for i, memory in enumerate(memories, 1):
            metadata = memory['metadata']
            timestamp = metadata.get('timestamp', 'Unknown time')
            text = memory['text']

            context_parts.append(
                f"\n{i}. [{timestamp}] {text}"
            )

        return "\n".join(context_parts)

    def _default_system_prompt(self) -> str:
        """Default system prompt for RAG."""
        return """You are Aurora AI, a helpful life optimization assistant.

You have access to the user's historical data and past interactions.
Use the provided context to give personalized, accurate responses.

Guidelines:
- Reference specific past events when relevant
- Be empathetic and understanding
- Provide actionable recommendations
- If context is insufficient, acknowledge it
- Keep responses concise but helpful

Always ground your responses in the provided context."""

    async def _generate_response(
        self,
        question: str,
        context: str,
        system_prompt: str
    ) -> str:
        """Generate response using LLM."""

        # Build prompt
        user_message = f"""Context from user's history:
{context}

User's question:
{question}

Please provide a helpful, personalized response based on the context."""

        # Generate with appropriate provider
        if self.llm_provider == "openai" and self.openai_client:
            response = await self._generate_openai(system_prompt, user_message)

        elif self.llm_provider == "anthropic" and self.anthropic_client:
            response = await self._generate_anthropic(system_prompt, user_message)

        else:
            response = "RAG system not properly configured. Please set up LLM provider."

        return response

    async def _generate_openai(self, system_prompt: str, user_message: str) -> str:
        """Generate response using OpenAI."""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating response: {str(e)}"

    async def _generate_anthropic(self, system_prompt: str, user_message: str) -> str:
        """Generate response using Anthropic."""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=self.model_name,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating response: {str(e)}"

    async def ask_with_timeframe(
        self,
        user_id: int,
        question: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Ask a question about a specific timeframe.

        Args:
            user_id: User ID
            question: Question
            days_back: How many days of history to consider

        Returns:
            Answer based on timeframe
        """
        # Get recent memories within timeframe
        recent_memories = self.memory_manager.get_recent_memories(
            user_id=user_id,
            limit=20
        )

        # Filter by timeframe
        cutoff_date = datetime.now() - timedelta(days=days_back)

        relevant_memories = [
            m for m in recent_memories
            if datetime.fromisoformat(m['metadata']['timestamp']) >= cutoff_date
        ]

        # Build context
        context = self._build_context(relevant_memories)

        # Generate response
        system_prompt = f"""You are analyzing the user's life data from the past {days_back} days.
Provide insights based on this recent timeframe."""

        response = await self._generate_response(
            question=question,
            context=context,
            system_prompt=system_prompt
        )

        return {
            'answer': response,
            'timeframe_days': days_back,
            'events_analyzed': len(relevant_memories),
            'timestamp': datetime.now().isoformat()
        }


class ConversationalAgent:
    """
    Conversational agent with memory.

    Maintains conversation history and uses RAG for context-aware responses.
    """

    def __init__(self, rag_system: RAGSystem):
        """
        Initialize conversational agent.

        Args:
            rag_system: RAG system instance
        """
        self.rag = rag_system
        self.conversation_history: Dict[int, List[Dict]] = {}

    async def chat(
        self,
        user_id: int,
        message: str,
        use_history: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with the agent.

        Args:
            user_id: User ID
            message: User's message
            use_history: Whether to use conversation history

        Returns:
            Agent's response
        """
        # Initialize conversation history if needed
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        # Add user message to history
        self.conversation_history[user_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })

        # Build system prompt with conversation context
        system_prompt = self._build_conversational_prompt(user_id, use_history)

        # Get response using RAG
        response = await self.rag.query(
            user_id=user_id,
            question=message,
            context_window=5,
            system_prompt=system_prompt
        )

        # Add assistant response to history
        self.conversation_history[user_id].append({
            'role': 'assistant',
            'content': response['answer'],
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 10 messages to avoid token limits
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

        return {
            'message': response['answer'],
            'sources': response['sources'],
            'conversation_turn': len(self.conversation_history[user_id]) // 2,
            'timestamp': datetime.now().isoformat()
        }

    def _build_conversational_prompt(self, user_id: int, use_history: bool) -> str:
        """Build system prompt with conversation history."""
        base_prompt = """You are Aurora AI, a supportive life optimization assistant.

You're having a conversation with the user. Be natural, empathetic, and helpful.
Reference past messages in this conversation when appropriate."""

        if not use_history or user_id not in self.conversation_history:
            return base_prompt

        # Add recent conversation history
        history = self.conversation_history[user_id][-6:]  # Last 3 exchanges

        if history:
            history_text = "\n\nRecent conversation:\n"
            for turn in history:
                role = "User" if turn['role'] == 'user' else "You"
                history_text += f"{role}: {turn['content']}\n"

            return base_prompt + history_text

        return base_prompt

    def clear_history(self, user_id: int):
        """Clear conversation history for a user."""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]

    def get_history(self, user_id: int) -> List[Dict]:
        """Get conversation history for a user."""
        return self.conversation_history.get(user_id, [])
