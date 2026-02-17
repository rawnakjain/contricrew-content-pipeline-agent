from crewai.project import CrewBase, agent, task, crew
from crewai import Agent, Task, Crew
from pydantic import BaseModel
from tools import web_search_tool

class ResearchState(BaseModel):
    topic: str = ""
    research: str = ""

@CrewBase
class ResearchCrew:

    def __init__(self, topic: str):
        self.topic = topic
    @agent
    def research_expert(self):
        return Agent(
            role="Head Researcher",
            backstory="You are a head researcher responsible for gathering information on a given topic to create content. You will use the provided topic to conduct research and gather relevant information that can be used to create high-quality content. Your research should be thorough and cover various aspects of the topic, including recent developments, key statistics, and expert opinions.",
            goal=f"Conduct research on the topic '{self.topic}' to gather relevant information that can be used to create high-quality content. Your research should be thorough and cover various aspects of the topic, including recent developments, key statistics, and expert opinions. The information you gather should be concise and directly related to the topic to ensure that it can be effectively utilized in the content creation process.",
            tools=[web_search_tool]
        )

    @task
    def conduct_research(self):
        return Task(
            description="""
            Conduct research on the topic '{self.state.topic}' to gather relevant information that can be used to create high-quality content. Your research should be thorough and cover various aspects of the topic, including recent developments, key statistics, and expert opinions. The information you gather should be concise and directly related to the topic to ensure that it can be effectively utilized in the content creation process.
            """,
            expected_output="A comprehensive research report that includes recent developments, key statistics, and expert opinions on the topic '{self.state.topic}'. The report should be concise and directly related to the topic to ensure that it can be effectively utilized in the content creation process.""",
            agent=self.research_expert(),
            output_pydantic=ResearchState
        )

    @crew
    def crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks
        )

