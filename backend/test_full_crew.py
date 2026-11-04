"""
DevTeam AI — Full Six-Agent Crew Execution Test.

Executes all six agents in sequential order using the shared Meta Muse Spark LLM:
1. Product Manager    -> Software Requirement Specification
2. Software Architect -> System Architecture Design
3. Database Designer  -> Database Schema & Model Design
4. Developer          -> Implementation & Source Code
5. Testing Engineer   -> Testing Report & Test Suite
6. Code Reviewer      -> Code Review & Security Report

Reuses:
- get_llm() from services.llm_service
- build_development_crew() from workflows.software_development_flow
- create_development_tasks() from tasks.development_tasks
- All six agent factory functions from agents.*
"""

import os
import sys
import traceback
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

from services.llm_service import get_llm
from workflows.software_development_flow import build_development_crew


def sanitize(text: str) -> str:
    """Ensure sensitive credentials are never exposed in output or errors."""
    api_key = os.getenv("META_API_KEY")
    if not text:
        return ""
    if api_key and len(api_key) > 4 and api_key in text:
        text = text.replace(api_key, "[REDACTED_API_KEY]")
    return text


def extract_output(task) -> str:
    """Safely extract raw text from a CrewAI task output object."""
    if hasattr(task, "output") and task.output is not None:
        return getattr(task.output, "raw", str(task.output)).strip()
    return ""


def run_full_crew_test() -> bool:
    print("=" * 70, flush=True)
    print("DevTeam AI — Full Six-Agent Crew Execution Test", flush=True)
    print("=" * 70, flush=True)

    # 1. Initialize shared Meta LLM
    print("\n[Step 1/4] Initializing shared Meta Muse Spark LLM (timeout=600s)...", flush=True)
    try:
        llm = get_llm()
        print("  Shared LLM initialized successfully.", flush=True)
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize shared LLM: {sanitize(str(e))}", flush=True)
        return False

    # 2. Build the six-agent crew using the existing crew builder
    print("\n[Step 2/4] Assembling full development crew (6 agents, 6 tasks)...", flush=True)
    try:
        crew = build_development_crew(llm=llm)
        print(f"  Agents ({len(crew.agents)}):", flush=True)
        for idx, agent in enumerate(crew.agents, start=1):
            print(f"    {idx}. {agent.role}", flush=True)
        print(f"  Tasks  ({len(crew.tasks)}): Sequential execution configured.", flush=True)
    except Exception as e:
        print(f"\n[ERROR] Failed to assemble crew: {sanitize(str(e))}", flush=True)
        return False

    # Attach real-time completion callbacks to all six tasks
    def make_task_callback(step_num: int, role: str):
        def _callback(output):
            print(f"\n[PROGRESS {step_num}/6] {role} has completed their task.", flush=True)
            raw_text = getattr(output, "raw", str(output)).strip()
            preview = raw_text[:160].replace("\n", " ").strip()
            if preview:
                print(f"  Summary preview: \"{sanitize(preview)}...\"", flush=True)
            print("-" * 70, flush=True)
        return _callback

    for idx, task in enumerate(crew.tasks, start=1):
        role = task.agent.role if task.agent else f"Agent {idx}"
        task.callback = make_task_callback(idx, role)

    # 3. Define test requirement
    test_requirement = (
        "Build a simple shopping platform where users can view products, "
        "add items to a cart, and place orders."
    )
    print("\n[Step 3/4] Test Input Requirement:", flush=True)
    print(f"  \"{test_requirement}\"", flush=True)

    # 4. Execute the sequential multi-agent crew
    print("\n[Step 4/4] Executing multi-agent collaboration...", flush=True)
    print("  Sequential pipeline: PM -> Architect -> DB Designer -> Developer -> QA -> Reviewer", flush=True)
    print("  Live task callbacks will print as each agent finishes.\n", flush=True)

    try:
        result = crew.kickoff(inputs={"user_requirement": test_requirement})

        print("\n" + "=" * 70, flush=True)
        print("ALL SIX TASKS COMPLETED SUCCESSFULLY", flush=True)
        print("=" * 70, flush=True)

        task_titles = [
            "Task 1 — Product Manager: Requirements Specification",
            "Task 2 — Software Architect: Architecture Design",
            "Task 3 — Database Designer: Database Schema & Models",
            "Task 4 — Developer: Code Implementation",
            "Task 5 — Testing Engineer: Test Plan & Test Suite",
            "Task 6 — Senior Code Reviewer: Code Review & Quality Report",
        ]

        for i, task in enumerate(crew.tasks):
            title = task_titles[i] if i < len(task_titles) else f"Task {i + 1}"
            output_content = extract_output(task)
            print("\n" + "-" * 70, flush=True)
            print(f"{title}", flush=True)
            print("-" * 70, flush=True)
            if output_content:
                print(sanitize(output_content), flush=True)
            else:
                print("(No output captured for this task)", flush=True)

        print("\n" + "=" * 70, flush=True)
        print("Final Crew Result Summary:", flush=True)
        print("=" * 70, flush=True)
        raw_result = getattr(result, "raw", str(result))
        print(sanitize(raw_result), flush=True)
        print("=" * 70, flush=True)

        print("\n[SUCCESS] Full six-agent collaboration test completed successfully!", flush=True)
        return True

    except KeyboardInterrupt:
        print("\n\n[INFO] Workflow cancelled by user (KeyboardInterrupt).", flush=True)
        print("Exiting test cleanly...", flush=True)
        return False
    except Exception as e:
        print("\n[ERROR] Crew execution failed:", flush=True)
        tb_str = traceback.format_exc()
        print(sanitize(tb_str), flush=True)
        return False


if __name__ == "__main__":
    success = run_full_crew_test()
    if not success:
        sys.exit(1)
