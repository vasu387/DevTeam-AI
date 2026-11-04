
from workflows.software_development_flow import (
    SoftwareDevelopmentFlow
)

flow = SoftwareDevelopmentFlow()

result = flow.kickoff(
    inputs={
        "user_requirement": "Build an online shopping platform"
    }
)

print("\nFINAL WORKFLOW RESULT:")
print(result)
