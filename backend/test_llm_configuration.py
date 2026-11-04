"""
Local LLM Configuration Test for DevTeam AI.

Verifies that the shared Meta Muse Spark LLM instance is created once
and assigned to all six specialized agents via Python object identity (`is`).

Does NOT call the Meta API or execute any CrewAI tasks.
"""

import sys
from services.llm_service import get_llm
from agents.product_manager import create_product_manager
from agents.software_architect import create_software_architect
from agents.database_designer import create_database_designer
from agents.developer import create_developer
from agents.testing_engineer import create_testing_engineer
from agents.code_reviewer import create_code_reviewer


def test_llm_configuration():
    print("\n==================================================")
    print("DEVTEAM AI - LOCAL LLM CONFIGURATION TEST")
    print("==================================================")

    # 1. Initialize shared LLM instance once
    print("\n1. Initializing shared LLM instance...")
    shared_llm = get_llm()
    print(f"   Model    : {shared_llm.model}")
    print(f"   Base URL : {shared_llm.base_url}")
    print(f"   LLM Type : {type(shared_llm).__name__}")
    print("   API Key  : [CONFIGURED]")

    # 2. Instantiate all six agents with the shared LLM
    print("\n2. Creating all six agents with the shared LLM...")
    agent_factories = [
        ("Product Manager", create_product_manager),
        ("Software Architect", create_software_architect),
        ("Database Designer", create_database_designer),
        ("Developer", create_developer),
        ("Testing Engineer", create_testing_engineer),
        ("Code Reviewer", create_code_reviewer),
    ]

    agents = []
    for name, factory in agent_factories:
        agent = factory(llm=shared_llm)
        agents.append((name, agent))
        print(f"   - Created agent: {name}")

    # 3. Verify exactly six agents are created
    print(f"\n3. Verifying agent count: {len(agents)} of 6 created.")
    assert len(agents) == 6, f"Expected 6 agents, found {len(agents)}"

    # 4. Verify identity comparison (is) for every agent's llm attribute
    print("\n4. Verifying shared LLM identity (`is`) for all agents:")
    for name, agent in agents:
        is_shared = agent.llm is shared_llm
        assert is_shared, f"Agent '{name}' does not share the exact LLM instance!"
        print(f"   [OK] {name:<20} -> agent.llm is shared_llm: True")

    # 5. Success message
    print("\n==================================================")
    print("[SUCCESS] All 6 agents share the exact same LLM instance!")
    print("==================================================\n")


if __name__ == "__main__":
    test_llm_configuration()

