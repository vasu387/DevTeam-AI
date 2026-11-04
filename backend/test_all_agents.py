
from agents.product_manager import create_product_manager
from agents.software_architect import create_software_architect
from agents.database_designer import create_database_designer
from agents.developer import create_developer
from agents.testing_engineer import create_testing_engineer
from agents.code_reviewer import create_code_reviewer


agents = [
    create_product_manager(),
    create_software_architect(),
    create_database_designer(),
    create_developer(),
    create_testing_engineer(),
    create_code_reviewer()
]

print("\nDEVTEAM AI - AGENT INITIALIZATION\n")

for index, agent in enumerate(agents, start=1):
    print(f"{index}. {agent.role}")
    print(f"   Goal: {agent.goal}\n")

print("All six CrewAI agents created successfully!")
