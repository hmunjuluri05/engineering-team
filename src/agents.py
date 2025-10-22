"""Agent definitions for the Engineering Team - Config-based approach."""

import yaml
import importlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from .tools import save_to_file


# Tool registry - maps tool names in YAML to actual Python functions
TOOL_REGISTRY = {
    'save_to_file': save_to_file,
}


class AgentFactory:
    """Factory class to create agents from YAML configuration."""

    def __init__(self, agents_config_path: str, tasks_config_path: str):
        """
        Initialize the AgentFactory.

        Args:
            agents_config_path: Path to the agents.yaml configuration file
            tasks_config_path: Path to the tasks.yaml configuration file
        """
        self.agents_config = self._load_yaml(agents_config_path)
        self.tasks_config = self._load_yaml(tasks_config_path)
        self.custom_tools_cache = {}  # Cache for loaded custom tools

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Dictionary containing the YAML configuration
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_custom_tools(self, module_name: str) -> Dict[str, Any]:
        """
        Load custom tools from a Python module.

        Args:
            module_name: Name of the module to import (e.g., "custom_tools")

        Returns:
            Dictionary mapping tool names to tool functions
        """
        if module_name in self.custom_tools_cache:
            return self.custom_tools_cache[module_name]

        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Extract all callable functions that don't start with underscore
            tools = {}
            for name in dir(module):
                if not name.startswith('_'):
                    attr = getattr(module, name)
                    if callable(attr):
                        tools[name] = attr

            self.custom_tools_cache[module_name] = tools
            return tools
        except ImportError as e:
            raise ValueError(f"Failed to import custom tools module '{module_name}': {e}")

    def _resolve_tools(self, tool_names: List[str], custom_tools_module: Optional[str] = None) -> List:
        """
        Resolve tool names to actual tool functions.

        Args:
            tool_names: List of tool names from the configuration
            custom_tools_module: Optional name of custom tools module to load

        Returns:
            List of tool functions
        """
        # Load custom tools if specified
        custom_tools = {}
        if custom_tools_module:
            custom_tools = self._load_custom_tools(custom_tools_module)

        tools = []
        for tool_name in tool_names:
            # Check custom tools first, then fall back to TOOL_REGISTRY
            if tool_name in custom_tools:
                tools.append(custom_tools[tool_name])
            elif tool_name in TOOL_REGISTRY:
                tools.append(TOOL_REGISTRY[tool_name])
            else:
                raise ValueError(
                    f"Tool '{tool_name}' not found in TOOL_REGISTRY or custom tools module"
                )
        return tools

    def _build_instruction(self, agent_name: str, task_name: str,
                          requirements: str) -> str:
        """
        Build the instruction for an agent by combining agent config and task config.

        Args:
            agent_name: Name of the agent
            task_name: Name of the task
            requirements: Project requirements

        Returns:
            Complete instruction string
        """
        agent_config = self.agents_config[agent_name]
        task_config = self.tasks_config[task_name]

        # Build instruction from role, goal, backstory, description, and expected_output
        instruction_parts = []

        # Add backstory (who the agent is)
        if 'backstory' in agent_config:
            backstory = agent_config['backstory'].strip()
            backstory = backstory.format(requirements=requirements)
            instruction_parts.append(backstory)

        # Add role
        if 'role' in agent_config:
            role = agent_config['role'].strip()
            role = role.format(requirements=requirements)
            instruction_parts.append(f"\nYour role: {role}")

        # Add goal
        if 'goal' in agent_config:
            goal = agent_config['goal'].strip()
            goal = goal.format(requirements=requirements)
            instruction_parts.append(f"\nYour goal: {goal}")

        # Add task description
        if 'description' in task_config:
            description = task_config['description'].strip()
            description = description.format(requirements=requirements)
            instruction_parts.append(f"\nTask: {description}")

        # Add expected output format
        if 'expected_output' in task_config:
            expected_output = task_config['expected_output'].strip()
            expected_output = expected_output.format(requirements=requirements)
            instruction_parts.append(f"\nExpected output: {expected_output}")

        # Add file saving instruction
        if 'output_file' in task_config:
            output_file = task_config['output_file'].strip()
            output_file = output_file.format(requirements=requirements)
            # Extract just the filename from the path
            filename = Path(output_file).name
            instruction_parts.append(
                f"\n\nWhen you complete your work, save it using the save_to_file tool with filename \"{filename}\"."
            )

        return "\n".join(instruction_parts)

    def create_agent(self, agent_name: str, task_name: str,
                    requirements: str) -> Agent:
        """
        Create an agent from configuration.

        Args:
            agent_name: Name of the agent in agents.yaml
            task_name: Name of the task in tasks.yaml
            requirements: Project requirements

        Returns:
            An Agent instance configured from the YAML files
        """
        if agent_name not in self.agents_config:
            raise ValueError(f"Agent '{agent_name}' not found in agents configuration")

        if task_name not in self.tasks_config:
            raise ValueError(f"Task '{task_name}' not found in tasks configuration")

        agent_config = self.agents_config[agent_name]

        # Build description from role
        description = agent_config.get('role', '').strip()
        description = description.format(requirements=requirements)

        # Build instruction
        instruction = self._build_instruction(
            agent_name, task_name, requirements
        )

        # Resolve tools (with optional custom tools module)
        tool_names = agent_config.get('tools', [])
        custom_tools_module = agent_config.get('custom_tools_module', None)
        tools = self._resolve_tools(tool_names, custom_tools_module)

        # Get model and output_key
        model = agent_config.get('model', 'gemini-2.0-flash-exp')
        output_key = agent_config.get('output_key', agent_name)

        return Agent(
            name=agent_name,
            model=model,
            description=description,
            instruction=instruction,
            tools=tools,
            output_key=output_key
        )

    def create_all_agents(self, requirements: str) -> Dict[str, Agent]:
        """
        Create all agents defined in the configuration.

        This method builds the agent-task mapping dynamically from tasks.yaml.
        Each task in tasks.yaml specifies which agent should execute it via the 'agent' field.

        Args:
            requirements: Project requirements

        Returns:
            Dictionary mapping agent names to Agent instances
        """
        # Build agent-task mapping from tasks.yaml (each task has an 'agent' field)
        agent_task_mapping = {}
        for task_name, task_config in self.tasks_config.items():
            if 'agent' in task_config:
                agent_name = task_config['agent']
                agent_task_mapping[agent_name] = task_name

        # Create all agents
        agents = {}
        for agent_name, task_name in agent_task_mapping.items():
            agents[agent_name] = self.create_agent(
                agent_name, task_name, requirements
            )

        return agents
