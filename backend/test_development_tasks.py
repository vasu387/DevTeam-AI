
from agents.product_manager import create_product_manager
from agents.software_architect import create_software_architect
from agents.database_designer import create_database_designer
from agents.developer import create_developer
from agents.testing_engineer import create_testing_engineer
from agents.code_reviewer import create_code_reviewer

from tasks.development_tasks import create_development_tasks


# Initialize all six agents
product_manager = create_product_manager()
software_architect = create_software_architect()
database_designer = create_database_designer()
developer = create_developer()
testing_engineer = create_testing_engineer()
code_reviewer = create_code_reviewer()


# Create all six tasks
tasks = create_development_tasks(
    product_manager,
    software_architect,
    database_designer,
    developer,
    testing_engineer,
    code_reviewer
)


print("\nDEVTEAM AI - TASK INITIALIZATION\n")

for index, task in enumerate(tasks, start=1):
    print(f"{index}. {task.agent.role}")
    print(f"   Expected output: {task.expected_output[:100]}...\n")

print("All six CrewAI tasks created successfully!")
