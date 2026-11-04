import os
import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Ensure isolated, sandbox-safe storage paths for CrewAI
storage_dir = BACKEND_DIR / ".crewai_storage"
storage_dir.mkdir(exist_ok=True)

os.environ["USERPROFILE"] = str(storage_dir)
os.environ["HOME"] = str(storage_dir)
os.environ["LOCALAPPDATA"] = str(storage_dir)
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

try:
    import appdirs

    appdirs.user_data_dir = lambda *a, **kw: str(storage_dir)
    appdirs.user_config_dir = lambda *a, **kw: str(storage_dir)
    appdirs.user_cache_dir = lambda *a, **kw: str(storage_dir)
    appdirs.user_state_dir = lambda *a, **kw: str(storage_dir)
    appdirs.user_log_dir = lambda *a, **kw: str(storage_dir)
except ImportError:
    pass

try:
    import crewai_core.settings

    crewai_core.settings.DEFAULT_CONFIG_PATH = storage_dir / "settings.json"
    crewai_core.settings.get_writable_config_path = lambda: storage_dir / "settings.json"
except ImportError:
    pass

from crewai import Crew, Process
try:
    from crewai.utilities.constants import NOT_SPECIFIED
except ImportError:
    NOT_SPECIFIED = object()

from services.llm_service import get_llm
from agents.product_manager import create_product_manager
from agents.software_architect import create_software_architect
from agents.database_designer import create_database_designer
from agents.developer import create_developer
from agents.testing_engineer import create_testing_engineer
from agents.code_reviewer import create_code_reviewer

from tasks.development_tasks import create_development_tasks
from workflows.software_development_flow import build_development_crew
from services.project_writer import write_project_files


def test_phase4_structure():
    print("\nStarting Phase 4 structural verification...\n")

    # 1. Create one shared LLM instance
    llm = get_llm()

    # 2. Construct all six agents using the same LLM
    agents = [
        create_product_manager(llm=llm),
        create_software_architect(llm=llm),
        create_database_designer(llm=llm),
        create_developer(llm=llm),
        create_testing_engineer(llm=llm),
        create_code_reviewer(llm=llm),
    ]

    assert len(agents) == 6
    assert all(agent.llm is llm for agent in agents)
    print("PASS: All six agents share the same LLM object.")

    # 3. Create all six tasks
    tasks = create_development_tasks(*agents)

    assert len(tasks) == 6
    print("PASS: Exactly six tasks created.")

    # 4. Verify task assignments
    for task, agent in zip(tasks, agents):
        assert task.agent is agent

    print("PASS: All tasks are assigned to the correct agents.")

    # 5. Verify task context relationships
    print("\nTask context inspection:")
    print(f"  Task 0 (requirements_task) context: {tasks[0].context!r} (type: {type(tasks[0].context).__name__})")
    print(f"  Task 1 (architecture_task) context count: {len(tasks[1].context) if isinstance(tasks[1].context, list) else 'N/A'}")
    print(f"  Task 2 (database_task) context count: {len(tasks[2].context) if isinstance(tasks[2].context, list) else 'N/A'}")
    print(f"  Task 3 (development_task) context count: {len(tasks[3].context) if isinstance(tasks[3].context, list) else 'N/A'}")
    print(f"  Task 4 (testing_task) context count: {len(tasks[4].context) if isinstance(tasks[4].context, list) else 'N/A'}")
    print(f"  Task 5 (review_task) context count: {len(tasks[5].context) if isinstance(tasks[5].context, list) else 'N/A'}\n")

    # Task 0 has no upstream tasks; in CrewAI it is represented by NOT_SPECIFIED sentinel, None, or []
    assert (
        tasks[0].context is None
        or tasks[0].context == []
        or tasks[0].context is NOT_SPECIFIED
        or repr(tasks[0].context) == "NOT_SPECIFIED"
    ), f"Task 0 context expected to be empty/unspecified, got {tasks[0].context!r}"

    assert tasks[1].context == [tasks[0]]
    assert tasks[2].context == [tasks[0], tasks[1]]
    assert tasks[3].context == [tasks[0], tasks[1], tasks[2]]
    assert tasks[4].context == [tasks[0], tasks[3]]
    assert tasks[5].context == [tasks[3], tasks[4]]

    print("PASS: All task context relationships are correct.")

    # 6. Build the crew without executing it
    crew = build_development_crew()

    assert isinstance(crew, Crew)
    assert len(crew.agents) == 6
    assert len(crew.tasks) == 6
    assert crew.process == Process.sequential

    print("PASS: Crew contains six agents and six tasks.")
    print("PASS: Crew uses sequential processing.")

    # 7. Verify project writer connection exists
    assert callable(write_project_files)

    print("PASS: Project writer function is available.")

    # IMPORTANT: Do not call crew.kickoff() here.
    print("\nAll Phase 4 structural checks passed!")
    print("No agents executed. No Meta API requests made.")


if __name__ == "__main__":
    test_phase4_structure()
