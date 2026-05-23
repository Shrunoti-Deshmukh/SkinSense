from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from skinsense.tools.Product_Search_Tool import ProductSearchTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Skinsense():
    """Skinsense crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def formulation_retriever(self) -> Agent:
        return Agent(
            config=self.agents_config['formulation_retriever'], # type: ignore[index]
            tools=[ProductSearchTool(), SerperDevTool()], 
            verbose=True
        )

    @agent
    def chemical_toxicologist(self) -> Agent:
        return Agent(
            config=self.agents_config['chemical_toxicologist'], # type: ignore[index]
            verbose=True
        )

    @agent
    def presentation_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['presentation_expert'],
            verbose=True
        )
    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def retrieve_ingredients_task(self) -> Task:
        return Task(
            config=self.tasks_config['retrieve_ingredients_task'],
            tools=[ProductSearchTool()] # type: ignore[index]
        )

    @task
    def analyze_chemical_safety_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_chemical_safety_task'], # type: ignore[index]
            context=[self.retrieve_ingredients_task()]
        )
    
    @task
    def generate_consumer_dashboard_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_consumer_dashboard_task'],
            context=[self.retrieve_ingredients_task(), self.analyze_chemical_safety_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Skinsense crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            use_native_tools=False
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
