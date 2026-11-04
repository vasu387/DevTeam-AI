"""
Test single agent execution (Product Manager) with shared Meta Muse Spark LLM.

Reuses:
- get_llm() from services.llm_service
- create_product_manager() from agents.product_manager
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

from crewai import Crew, Task, Process
from services.llm_service import get_llm
from agents.product_manager import create_product_manager


def sanitize(text: str) -> str:
    """Ensure the API key is never exposed in output or error messages."""
    api_key = os.getenv("META_API_KEY")
    if not text:
        return ""
    if api_key and len(api_key) > 4 and api_key in text:
        text = text.replace(api_key, "[REDACTED_API_KEY]")
    return text


def run_single_agent_test():
    print("=" * 60)
    print("DevTeam AI — Single Agent Execution Test (Product Manager)")
    print("=" * 60)

    # 1. Initialize the shared Meta LLM
    print("\n[1/4] Initializing Meta Muse Spark LLM...")
    try:
        llm = get_llm()
        print("  LLM initialized successfully.")
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize LLM: {sanitize(str(e))}")
        sys.exit(1)

    # 2. Instantiate the Product Manager agent
    print("\n[2/4] Instantiating Product Manager agent...")
    try:
        product_manager = create_product_manager(llm=llm)
        print(f"  Agent Role: {product_manager.role}")
    except Exception as e:
        print(f"\n[ERROR] Failed to create Product Manager agent: {sanitize(str(e))}")
        sys.exit(1)

    # 3. Create test task
    print("\n[3/4] Defining test task...")
    test_task = Task(
        description=(
            "Identify the purpose and three core features of a simple shopping platform. "
            "Be clear, concise, and structured."
        ),
        expected_output=(
            "A concise document clearly stating the platform's purpose and three core features."
        ),
        agent=product_manager,
    )

    crew = Crew(
        agents=[product_manager],
        tasks=[test_task],
        process=Process.sequential,
        verbose=True,
    )

    # 4. Execute the agent task
    print("\n[4/4] Executing task with Product Manager...")
    try:
        result = crew.kickoff()
        output_text = getattr(result, "raw", str(result))

        print("\n" + "=" * 60)
        print("Product Manager Output:")
        print("=" * 60)
        print(sanitize(output_text))
        print("=" * 60)
        print("\n[SUCCESS] Single agent execution test completed successfully!")

    except Exception as e:
        print("\n[ERROR] Agent execution failed:")
        tb_str = traceback.format_exc()
        print(sanitize(tb_str))
        sys.exit(1)


if __name__ == "__main__":
    run_single_agent_test()

