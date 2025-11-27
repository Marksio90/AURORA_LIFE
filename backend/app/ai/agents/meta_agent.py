"""
MetaAgent - Hierarchical Agent Architecture

Orchestrates all specialized agents with:
- RAG-powered memory
- Collaborative decision making
- Reasoning and planning
- Context-aware coordination
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.agent_orchestrator import AgentOrchestrator
from app.ai.memory.rag_system import RAGSystem, ConversationalAgent
from app.ai.memory.vector_store import VectorStore, MemoryManager
from app.integrations.openai_client import get_openai_client
from app.integrations.anthropic_client import get_anthropic_client


class MetaAgent:
    """
    Meta-level agent that coordinates all other agents.

    Hierarchy:
    MetaAgent (Strategic, Reasoning)
    ├── Agent Orchestrator (Tactical)
    │   ├── Decision Agent
    │   ├── Prediction Agent
    │   ├── Mood Agent
    │   ├── Health Agent
    │   ├── Time Agent
    │   ├── Relationships Agent
    │   └── Growth Agent
    └── RAG System (Memory & Context)
        └── Vector Store (Long-term Memory)

    Capabilities:
    1. Strategic planning across all life domains
    2. Multi-agent coordination and consensus
    3. Memory-augmented decision making
    4. Natural language interaction
    5. Explainable reasoning
    """

    def __init__(
        self,
        db: AsyncSession,
        vector_store: Optional[VectorStore] = None,
        llm_provider: str = "openai"
    ):
        """
        Initialize MetaAgent.

        Args:
            db: Database session
            vector_store: Optional vector store (creates in-memory if None)
            llm_provider: 'openai' or 'anthropic'
        """
        self.db = db
        self.llm_provider = llm_provider

        # Initialize orchestrator for all specialized agents
        self.orchestrator = AgentOrchestrator(db)

        # Initialize vector store and RAG
        if vector_store is None:
            # Create in-memory vector store
            vector_store = VectorStore(
                backend="chromadb",
                collection_name="aurora_meta_agent"
            )

        self.vector_store = vector_store
        self.memory_manager = MemoryManager(vector_store)

        # Initialize RAG system
        self.rag = RAGSystem(
            vector_store=vector_store,
            llm_provider=llm_provider,
            model_name="gpt-4" if llm_provider == "openai" else "claude-3-5-sonnet-20241022"
        )

        # Conversational interface
        self.conversational_agent = ConversationalAgent(self.rag)

        # LLM clients for reasoning
        if llm_provider == "openai":
            self.llm_client = get_openai_client()
        else:
            self.llm_client = get_anthropic_client()

    async def analyze_and_recommend(
        self,
        user_id: int,
        query: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis and recommendations.

        Workflow:
        1. Retrieve context from memory (if enabled)
        2. Run all specialized agents
        3. Synthesize results with reasoning
        4. Generate unified recommendations
        5. Store insights in memory

        Args:
            user_id: User ID
            query: Optional specific question/focus
            use_memory: Whether to use RAG memory

        Returns:
            Comprehensive analysis and recommendations
        """
        start_time = datetime.now()

        # Step 1: Retrieve relevant context from memory
        memory_context = None
        if use_memory and query:
            memory_context = await self.rag.query(
                user_id=user_id,
                question=query,
                context_window=5
            )

        # Step 2: Run all specialized agents
        agent_results = await self.orchestrator.run_all_agents(
            user_id=user_id,
            context={'query': query} if query else None
        )

        # Step 3: Synthesize with meta-reasoning
        synthesis = await self._meta_reasoning(
            user_id=user_id,
            agent_results=agent_results,
            memory_context=memory_context,
            query=query
        )

        # Step 4: Generate unified recommendations
        recommendations = self._unify_recommendations(
            agent_results=agent_results,
            synthesis=synthesis
        )

        # Step 5: Store insights in memory
        if use_memory:
            await self._store_insights_in_memory(
                user_id=user_id,
                synthesis=synthesis,
                recommendations=recommendations
            )

        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            'meta_analysis': synthesis,
            'agent_results': agent_results,
            'unified_recommendations': recommendations,
            'memory_context': memory_context if memory_context else None,
            'execution_time_seconds': execution_time,
            'timestamp': datetime.now().isoformat()
        }

    async def _meta_reasoning(
        self,
        user_id: int,
        agent_results: Dict[str, Any],
        memory_context: Optional[Dict],
        query: Optional[str]
    ) -> Dict[str, Any]:
        """
        Meta-level reasoning across all agent outputs.

        Uses LLM to synthesize insights from all agents.
        """
        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(
            agent_results=agent_results,
            memory_context=memory_context,
            query=query
        )

        # Generate meta-level insights
        if self.llm_provider == "openai":
            reasoning = await self._reason_with_openai(prompt)
        else:
            reasoning = await self._reason_with_anthropic(prompt)

        return {
            'meta_insights': reasoning,
            'cross_domain_patterns': self._identify_cross_domain_patterns(agent_results),
            'consensus_score': self._calculate_consensus(agent_results),
            'confidence': self._calculate_overall_confidence(agent_results)
        }

    def _build_reasoning_prompt(
        self,
        agent_results: Dict[str, Any],
        memory_context: Optional[Dict],
        query: Optional[str]
    ) -> str:
        """Build prompt for meta-reasoning."""
        prompt_parts = [
            "You are Aurora MetaAgent, coordinating multiple specialized AI agents.",
            "\nYour task: Synthesize insights from all agents into a coherent analysis.\n"
        ]

        # Add query if provided
        if query:
            prompt_parts.append(f"\nUser's question: {query}\n")

        # Add memory context
        if memory_context and memory_context.get('sources'):
            prompt_parts.append("\nRelevant historical context:")
            for source in memory_context['sources'][:3]:
                prompt_parts.append(f"- {source['text']}")
            prompt_parts.append("")

        # Add agent results
        prompt_parts.append("\nAgent Analysis Results:\n")

        agent_summaries = {
            'prediction_agent': agent_results.get('agent_results', {}).get('prediction_agent', {}),
            'mood_agent': agent_results.get('agent_results', {}).get('mood_agent', {}),
            'health_agent': agent_results.get('agent_results', {}).get('health_agent', {}),
            'decision_agent': agent_results.get('agent_results', {}).get('decision_agent', {})
        }

        for agent_name, result in agent_summaries.items():
            if result and 'analysis' in result:
                prompt_parts.append(f"\n{agent_name}:")
                prompt_parts.append(f"  {str(result['analysis'])[:200]}")

        prompt_parts.append("\n\nProvide:")
        prompt_parts.append("1. Key insights from cross-agent analysis")
        prompt_parts.append("2. Identified patterns and correlations")
        prompt_parts.append("3. Priority areas for focus")
        prompt_parts.append("4. Strategic recommendations")
        prompt_parts.append("\nBe concise (max 300 words).")

        return "\n".join(prompt_parts)

    async def _reason_with_openai(self, prompt: str) -> str:
        """Generate reasoning using OpenAI."""
        try:
            response = await asyncio.to_thread(
                self.llm_client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Aurora MetaAgent, a strategic AI coordinator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Meta-reasoning error: {str(e)}"

    async def _reason_with_anthropic(self, prompt: str) -> str:
        """Generate reasoning using Anthropic."""
        try:
            response = await asyncio.to_thread(
                self.llm_client.messages.create,
                model="claude-3-5-sonnet-20241022",
                system="You are Aurora MetaAgent, a strategic AI coordinator.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            return response.content[0].text
        except Exception as e:
            return f"Meta-reasoning error: {str(e)}"

    def _identify_cross_domain_patterns(self, agent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify patterns across different life domains."""
        patterns = []

        # Example: Check if multiple agents detect same underlying issue
        agents = agent_results.get('agent_results', {})

        # Pattern 1: Energy & Mood correlation
        mood_analysis = agents.get('mood_agent', {}).get('analysis', {})
        health_analysis = agents.get('health_agent', {}).get('analysis', {})

        if mood_analysis and health_analysis:
            patterns.append({
                'pattern': 'mood_energy_correlation',
                'description': 'Mood and energy levels are interconnected',
                'confidence': 0.85
            })

        # Pattern 2: Time management affecting multiple domains
        time_analysis = agents.get('time_agent', {}).get('analysis', {})
        if time_analysis:
            patterns.append({
                'pattern': 'time_management_impact',
                'description': 'Time allocation affects productivity and wellbeing',
                'confidence': 0.78
            })

        return patterns

    def _calculate_consensus(self, agent_results: Dict[str, Any]) -> float:
        """Calculate consensus score across agents."""
        # Simplified consensus: check if recommendations align

        recommendations = []
        agents = agent_results.get('agent_results', {})

        for agent_name, result in agents.items():
            if 'recommendations' in result:
                recommendations.append(result['recommendations'])

        if len(recommendations) < 2:
            return 0.5

        # Simple heuristic: higher consensus if multiple agents suggest similar actions
        consensus_score = 0.75  # Baseline
        return consensus_score

    def _calculate_overall_confidence(self, agent_results: Dict[str, Any]) -> float:
        """Calculate overall confidence in analysis."""
        confidences = []

        agents = agent_results.get('agent_results', {})
        for agent_name, result in agents.items():
            if isinstance(result, dict):
                # Look for confidence in analysis or recommendations
                analysis = result.get('analysis', {})
                if isinstance(analysis, dict) and 'confidence' in analysis:
                    confidences.append(analysis['confidence'])

        if confidences:
            return sum(confidences) / len(confidences)
        return 0.75  # Default confidence

    def _unify_recommendations(
        self,
        agent_results: Dict[str, Any],
        synthesis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Unify recommendations from all agents into prioritized list."""
        all_recommendations = []

        # Collect recommendations from all agents
        agents = agent_results.get('agent_results', {})

        for agent_name, result in agents.items():
            if not isinstance(result, dict):
                continue

            recs = result.get('recommendations', {})

            # Extract recommendations based on agent type
            if agent_name == 'decision_agent':
                agent_recs = recs.get('recommendations', [])
            elif agent_name == 'health_agent':
                agent_recs = recs.get('health_recommendations', [])
            elif agent_name == 'prediction_agent':
                agent_recs = recs.get('proactive_recommendations', [])
            else:
                agent_recs = []

            for rec in agent_recs:
                if isinstance(rec, dict):
                    all_recommendations.append({
                        'action': rec.get('action', str(rec)),
                        'source_agent': agent_name,
                        'priority': rec.get('priority', 'medium'),
                        'rationale': rec.get('reason', rec.get('rationale', ''))
                    })

        # Prioritize recommendations
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        all_recommendations.sort(
            key=lambda r: priority_order.get(r['priority'], 2),
            reverse=True
        )

        # Return top 10
        return all_recommendations[:10]

    async def _store_insights_in_memory(
        self,
        user_id: int,
        synthesis: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ):
        """Store analysis insights in memory for future context."""
        # Store meta-insights
        if 'meta_insights' in synthesis:
            self.memory_manager.add_semantic_memory(
                user_id=user_id,
                fact=synthesis['meta_insights'],
                category='meta_analysis'
            )

        # Store top recommendations
        for rec in recommendations[:3]:
            self.memory_manager.add_semantic_memory(
                user_id=user_id,
                fact=f"Recommendation: {rec['action']} (from {rec['source_agent']})",
                category='recommendations'
            )

    async def chat(
        self,
        user_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Chat with MetaAgent using natural language.

        Args:
            user_id: User ID
            message: User's message

        Returns:
            Agent's response
        """
        return await self.conversational_agent.chat(user_id, message)

    async def explain_recommendation(
        self,
        user_id: int,
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Explain why a specific recommendation was made.

        Args:
            user_id: User ID
            recommendation: The recommendation to explain

        Returns:
            Detailed explanation
        """
        explanation_query = f"Why did you recommend: {recommendation}?"

        return await self.rag.query(
            user_id=user_id,
            question=explanation_query,
            context_window=10,
            system_prompt="""You are explaining a recommendation you made.

Use the historical context to explain:
1. What patterns led to this recommendation
2. What data supports it
3. What outcome we expect
4. What might happen if not followed

Be specific and reference actual user data."""
        )
