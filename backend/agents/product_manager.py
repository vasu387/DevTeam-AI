
from crewai import Agent
from pathlib import Path
import yaml


# Load agent configuration
CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "agents.yaml"
)

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)


# Create Product Manager Agent
def create_product_manager(llm=None):

    agent_config = config["product_manager"]

    product_manager = Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        verbose=agent_config["verbose"],
        llm=llm
    )

    return product_manager
