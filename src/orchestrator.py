"""Orchestrator for the Engineering Team with parallel execution support."""

from pathlib import Path
from google.adk.agents import SequentialAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from .agents import AgentFactory


class EngineeringTeam:
    """
    Engineering Team orchestrator using Google ADK.

    This class creates a two-phase workflow:
    1. Design Phase: Engineering Lead creates the design (sequential)
    2. Implementation Phase: Backend, Frontend, and Test engineers work in parallel from the design

    Architecture:
    - Uses SequentialAgent for overall workflow (Phase 1 then Phase 2)
    - Uses ParallelAgent for Phase 2 to run Backend, Frontend, Test simultaneously
    - Agents communicate through shared state using output_key
    - Agents are created from YAML configuration files
    """

    def __init__(self, requirements: str,
                 agents_config: str = None, tasks_config: str = None):
        """
        Initialize the Engineering Team.

        Args:
            requirements: The project requirements
            agents_config: Path to agents.yaml (defaults to src/config/agents.yaml)
            tasks_config: Path to tasks.yaml (defaults to src/config/tasks.yaml)
        """
        self.requirements = requirements

        # Set default config paths if not provided
        if agents_config is None:
            config_dir = Path(__file__).parent / 'config'
            agents_config = str(config_dir / 'agents.yaml')

        if tasks_config is None:
            config_dir = Path(__file__).parent / 'config'
            tasks_config = str(config_dir / 'tasks.yaml')

        # Create the agent factory
        self.agent_factory = AgentFactory(agents_config, tasks_config)

        # Create all agents from configuration
        agents_dict = self.agent_factory.create_all_agents(requirements)

        # Store individual agents
        self.engineering_lead = agents_dict['engineering_lead']
        self.backend_engineer = agents_dict['backend_engineer']
        self.frontend_engineer = agents_dict['frontend_engineer']
        self.test_engineer = agents_dict['test_engineer']

        # Create parallel implementation team
        # Backend, Frontend, and Test run simultaneously since they all depend only on design
        self.implementation_team = ParallelAgent(
            name="implementation_team",
            description="Backend, Frontend, and Test engineers working in parallel from the design",
            sub_agents=[
                self.backend_engineer,
                self.frontend_engineer,
                self.test_engineer
            ]
        )

        # Create the overall workflow
        # Phase 1: Design (Engineering Lead runs first)
        # Phase 2: Implementation (Backend, Frontend, Test run in parallel)
        self.team = SequentialAgent(
            name="engineering_team",
            description="Complete engineering team: sequential design, then parallel implementation",
            sub_agents=[
                self.engineering_lead,
                self.implementation_team
            ]
        )

    def run(self, user_query: str = None) -> dict:
        """
        Run the engineering team workflow in two phases:
        1. Design Phase: Engineering Lead creates DESIGN.md (sequential)
        2. Implementation Phase: Backend, Frontend, Test work in parallel from the design

        Uses SequentialAgent for the overall workflow (design then implementation)
        and ParallelAgent for Phase 2 to run Backend, Frontend, Test simultaneously.

        Args:
            user_query: Optional user query to start the workflow

        Returns:
            A dictionary containing the results from the workflow
        """
        if user_query is None:
            user_query = f"Create a complete software solution based on these requirements:\n\n{self.requirements}"

        print("\n" + "="*80)
        print("RUNNING ENGINEERING TEAM WORKFLOW")
        print("="*80)
        print("Phase 1: Design (Engineering Lead - Sequential)")
        print("Phase 2: Implementation (Backend, Frontend, Test - Parallel)")
        print("="*80)

        # Create a single runner for the entire team
        runner = InMemoryRunner(
            agent=self.team,
            app_name="engineering_team"
        )

        # Create a session
        session = runner.session_service.create_session_sync(
            app_name="engineering_team",
            user_id="user1"
        )

        # Run the complete workflow
        content = types.Content(parts=[types.Part(text=user_query)])
        final_result = None

        for event in runner.run(
            user_id="user1",
            session_id=session.id,
            new_message=content
        ):
            # Print progress as agents execute
            if hasattr(event, 'agent_name') and event.agent_name:
                print(f"\n>>> Agent: {event.agent_name}")

            if event.is_final_response() and event.content:
                final_result = event.content.parts[0].text

        # Return results
        result = {
            'status': 'completed',
            'final_output': final_result
        }

        return result
