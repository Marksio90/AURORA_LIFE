"""
FlowOS-style AI Orchestrator for multi-agent workflows.

Coordinates multiple AI agents to handle complex tasks:
- Task decomposition
- Agent coordination
- Result synthesis
- Context management
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
import asyncio
import logging

from app.integrations.openai_client import OpenAIClient
from app.integrations.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Available agent types."""
    ANALYST = "analyst"  # Data analysis and insights
    PLANNER = "planner"  # Goal planning and scheduling
    ADVISOR = "advisor"  # Decision support and recommendations
    RESEARCHER = "researcher"  # Information gathering
    SYNTHESIZER = "synthesizer"  # Result combination


@dataclass
class Task:
    """Represents a task in the workflow."""
    id: UUID
    type: AgentType
    description: str
    context: Dict[str, Any]
    dependencies: List[UUID]
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: UUID
    tasks_completed: int
    tasks_failed: int
    final_result: Dict[str, Any]
    execution_time: float
    task_results: Dict[str, Any]


class Agent:
    """Base agent class."""

    def __init__(self, agent_type: AgentType, use_claude: bool = False):
        self.agent_type = agent_type
        self.openai_client = OpenAIClient()
        self.claude_client = ClaudeClient()
        self.use_claude = use_claude

    async def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task.

        Args:
            task: Task to execute
            context: Execution context including previous results

        Returns:
            Task result
        """
        prompt = self._build_prompt(task, context)

        if self.use_claude:
            response = await self.claude_client.generate(prompt, max_tokens=2000)
        else:
            response = await self.openai_client.generate(prompt, max_tokens=2000)

        return {
            "agent_type": self.agent_type.value,
            "task_id": str(task.id),
            "output": response,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _build_prompt(self, task: Task, context: Dict[str, Any]) -> str:
        """Build prompt for the agent."""
        system_prompts = {
            AgentType.ANALYST: """You are a data analyst agent. Analyze user data and identify patterns, trends, and insights.
Provide specific, data-driven observations.""",

            AgentType.PLANNER: """You are a planning agent. Create actionable plans based on goals and constraints.
Break down complex goals into concrete steps with timelines.""",

            AgentType.ADVISOR: """You are an advisory agent. Provide thoughtful recommendations based on analysis.
Consider trade-offs and present balanced perspectives.""",

            AgentType.RESEARCHER: """You are a research agent. Gather and synthesize relevant information.
Provide comprehensive context for decision-making.""",

            AgentType.SYNTHESIZER: """You are a synthesis agent. Combine insights from multiple sources into coherent conclusions.
Create unified, actionable outputs."""
        }

        base_prompt = system_prompts.get(self.agent_type, "You are a helpful AI assistant.")

        # Add context from previous tasks
        context_str = ""
        if context.get("previous_results"):
            context_str = "\n\nPrevious Results:\n"
            for result in context["previous_results"]:
                context_str += f"- {result.get('agent_type')}: {result.get('output', '')[:200]}...\n"

        # Add user data context
        user_data_str = ""
        if context.get("user_data"):
            user_data_str = f"\n\nUser Data:\n{context['user_data']}\n"

        return f"""{base_prompt}

Task: {task.description}
{user_data_str}{context_str}

Please provide your analysis/output:"""


class FlowOSOrchestrator:
    """
    FlowOS-style orchestrator for coordinating multi-agent workflows.

    Features:
    - Automatic task decomposition
    - Parallel and sequential execution
    - Dependency management
    - Result synthesis
    """

    def __init__(self):
        self.agents: Dict[AgentType, Agent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize agent pool."""
        for agent_type in AgentType:
            # Use Claude for advisor and synthesizer, OpenAI for others
            use_claude = agent_type in [AgentType.ADVISOR, AgentType.SYNTHESIZER]
            self.agents[agent_type] = Agent(agent_type, use_claude=use_claude)

    async def execute_workflow(
        self,
        objective: str,
        user_data: Dict[str, Any],
        workflow_type: str = "auto"
    ) -> WorkflowResult:
        """
        Execute a multi-agent workflow.

        Args:
            objective: High-level objective
            user_data: User context and data
            workflow_type: Type of workflow (auto, analysis, planning, decision)

        Returns:
            Workflow result
        """
        workflow_id = uuid4()
        start_time = datetime.utcnow()

        logger.info(f"Starting workflow {workflow_id}: {objective}")

        # Decompose objective into tasks
        tasks = await self._decompose_objective(objective, workflow_type)

        # Execute tasks with dependency management
        task_results = await self._execute_tasks(tasks, user_data)

        # Synthesize results
        final_result = await self._synthesize_results(objective, task_results)

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        completed = sum(1 for t in tasks if t.status == "completed")
        failed = sum(1 for t in tasks if t.status == "failed")

        return WorkflowResult(
            workflow_id=workflow_id,
            tasks_completed=completed,
            tasks_failed=failed,
            final_result=final_result,
            execution_time=execution_time,
            task_results={str(t.id): t.result for t in tasks if t.result}
        )

    async def _decompose_objective(
        self,
        objective: str,
        workflow_type: str
    ) -> List[Task]:
        """
        Decompose high-level objective into tasks.

        Args:
            objective: High-level objective
            workflow_type: Type of workflow

        Returns:
            List of tasks with dependencies
        """
        # Predefined workflow templates
        workflows = {
            "analysis": [
                (AgentType.RESEARCHER, "Gather relevant data and context", []),
                (AgentType.ANALYST, "Analyze data and identify patterns", [0]),
                (AgentType.SYNTHESIZER, "Synthesize findings into insights", [1])
            ],
            "planning": [
                (AgentType.ANALYST, "Analyze current state and constraints", []),
                (AgentType.PLANNER, "Create detailed action plan", [0]),
                (AgentType.ADVISOR, "Review plan and provide recommendations", [1]),
                (AgentType.SYNTHESIZER, "Finalize comprehensive plan", [1, 2])
            ],
            "decision": [
                (AgentType.RESEARCHER, "Research options and alternatives", []),
                (AgentType.ANALYST, "Analyze pros/cons of each option", [0]),
                (AgentType.ADVISOR, "Provide decision recommendations", [0, 1]),
                (AgentType.SYNTHESIZER, "Synthesize final recommendation", [1, 2])
            ]
        }

        # Select workflow
        template = workflows.get(workflow_type, workflows["analysis"])

        # Create tasks
        tasks = []
        task_ids = []

        for idx, (agent_type, description, deps) in enumerate(template):
            task_id = uuid4()
            task_ids.append(task_id)

            # Resolve dependencies
            dep_ids = [task_ids[d] for d in deps if d < len(task_ids)]

            task = Task(
                id=task_id,
                type=agent_type,
                description=f"{description} - {objective}",
                context={},
                dependencies=dep_ids
            )

            tasks.append(task)

        return tasks

    async def _execute_tasks(
        self,
        tasks: List[Task],
        user_data: Dict[str, Any]
    ) -> List[Task]:
        """
        Execute tasks with dependency management.

        Args:
            tasks: List of tasks to execute
            user_data: User context

        Returns:
            Completed tasks with results
        """
        completed_tasks = {}
        pending_tasks = {str(t.id): t for t in tasks}

        while pending_tasks:
            # Find tasks ready to execute (dependencies met)
            ready_tasks = []

            for task_id, task in pending_tasks.items():
                if all(str(dep_id) in completed_tasks for dep_id in task.dependencies):
                    ready_tasks.append(task)

            if not ready_tasks:
                logger.error("Circular dependency or stuck workflow")
                break

            # Execute ready tasks in parallel
            async def execute_task(task: Task):
                try:
                    task.status = "in_progress"
                    task.started_at = datetime.utcnow()

                    # Build context with previous results
                    context = {
                        "user_data": user_data,
                        "previous_results": [
                            completed_tasks[str(dep_id)].result
                            for dep_id in task.dependencies
                            if str(dep_id) in completed_tasks
                        ]
                    }

                    # Execute agent
                    agent = self.agents[task.type]
                    result = await agent.execute(task, context)

                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()

                    logger.info(f"Task {task.id} completed: {task.type.value}")

                except Exception as e:
                    logger.error(f"Task {task.id} failed: {str(e)}")
                    task.status = "failed"
                    task.result = {"error": str(e)}

                return task

            # Execute ready tasks concurrently
            results = await asyncio.gather(*[execute_task(t) for t in ready_tasks])

            # Update completed tasks
            for task in results:
                completed_tasks[str(task.id)] = task
                del pending_tasks[str(task.id)]

        return list(completed_tasks.values())

    async def _synthesize_results(
        self,
        objective: str,
        tasks: List[Task]
    ) -> Dict[str, Any]:
        """
        Synthesize results from all tasks.

        Args:
            objective: Original objective
            tasks: Completed tasks

        Returns:
            Synthesized result
        """
        # Get synthesizer agent
        synthesizer = self.agents[AgentType.SYNTHESIZER]

        # Build synthesis context
        all_outputs = "\n\n".join([
            f"**{t.type.value.upper()}**:\n{t.result.get('output', '')}"
            for t in tasks
            if t.result and t.status == "completed"
        ])

        synthesis_task = Task(
            id=uuid4(),
            type=AgentType.SYNTHESIZER,
            description=f"Synthesize all findings for: {objective}",
            context={"all_outputs": all_outputs},
            dependencies=[]
        )

        # Execute synthesis
        context = {
            "previous_results": [t.result for t in tasks if t.result],
            "objective": objective
        }

        result = await synthesizer.execute(synthesis_task, context)

        return {
            "objective": objective,
            "synthesis": result["output"],
            "contributing_agents": [t.type.value for t in tasks if t.status == "completed"],
            "total_tasks": len(tasks),
            "successful_tasks": sum(1 for t in tasks if t.status == "completed")
        }


# Usage examples:
"""
from app.ai.orchestrator import FlowOSOrchestrator

# Initialize orchestrator
orchestrator = FlowOSOrchestrator()

# Execute analysis workflow
result = await orchestrator.execute_workflow(
    objective="Analyze my productivity patterns and suggest improvements",
    user_data={
        "events": [...],
        "metrics": {...},
        "goals": [...]
    },
    workflow_type="analysis"
)

print(result.final_result["synthesis"])

# Execute planning workflow
result = await orchestrator.execute_workflow(
    objective="Create a plan to improve my sleep quality",
    user_data={...},
    workflow_type="planning"
)

# Execute decision workflow
result = await orchestrator.execute_workflow(
    objective="Should I take on this new project?",
    user_data={...},
    workflow_type="decision"
)
"""
