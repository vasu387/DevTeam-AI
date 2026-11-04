
from crewai import Agent
from pathlib import Path
import yaml

CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "agents.yaml"
)

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


def create_testing_engineer(llm=None):

    agent_config = config["testing_engineer"]

    testing_engineer = Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        verbose=agent_config["verbose"],
        llm=llm
    )

    return testing_engineer
