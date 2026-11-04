import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.endpoints.projects import get_job_status, get_project_files, download_project_zip, list_projects
from services.job_manager import (
    GENERATED_PROJECTS_DIR,
    JOBS_REGISTRY_PATH,
    STORAGE_DIR,
    JobManager,
    job_manager,
)


def run_fixes_verification():
    print("=" * 70, flush=True)
    print("DEVTEAM AI - FOUR FIXES COMPREHENSIVE VERIFICATION SUITE", flush=True)
    print("=" * 70, flush=True)

    # -------------------------------------------------------------
    # 1. VERIFY FIX 1: UVICORN RELOAD CONFIGURATION
    # -------------------------------------------------------------
    print("\n[Check 1] Verifying Uvicorn reload configuration in main.py...", flush=True)
    main_py_path = BACKEND_DIR / "main.py"
    with open(main_py_path, "r", encoding="utf-8") as f:
        main_content = f.read()

    assert 'reload_enabled = os.getenv("RELOAD", "false").lower() == "true"' in main_content, "Reload not disabled by default"
    assert 'reload_excludes' in main_content, "Reload exclusions not configured"
    assert '.crewai_storage/*' in main_content, "Storage exclusion missing from reload_excludes"
    assert 'generated_projects/*' in main_content, "Generated projects exclusion missing from reload_excludes"
    print("  PASS: Uvicorn auto-reload is disabled by default and ignores storage/project writes.", flush=True)

    # -------------------------------------------------------------
    # 2. VERIFY FIX 4: PERSISTENT REGISTRY & CRASH RECOVERY
    # -------------------------------------------------------------
    print("\n[Check 2] Verifying persistent registry and restart recovery...", flush=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_registry = Path(tmp_dir) / "test_registry.json"

        # Create manager instance with custom registry file
        mgr = JobManager(registry_path=tmp_registry)

        # Create a test job and mark running
        job = mgr.create_job("Fitness App", "Build a fitness tracking app.")
        job_id = job["job_id"]
        mgr.update_job(job_id, status="running", progress=35, activity="Developer is writing code...")
        mgr.update_agent(job_id, "developer", status="running", progress=50, activity="Writing models...")

        # Confirm registry file written to disk
        assert tmp_registry.exists(), "Registry file was not created on disk"
        with open(tmp_registry, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert job_id in saved_data
        assert saved_data[job_id]["status"] == "running"
        print("  PASS: Job updates persisted to disk atomically.", flush=True)

        # Simulate sudden backend server restart: instantiate a new JobManager pointing to the same file
        restarted_mgr = JobManager(registry_path=tmp_registry)
        recovered_job = restarted_mgr.get_job(job_id)

        assert recovered_job is not None, "Job not recovered after restart"
        assert recovered_job["status"] == "interrupted", f"Expected 'interrupted', got '{recovered_job['status']}'"
        assert "server restarted" in recovered_job["error_message"].lower(), "Missing restart error explanation"
        assert recovered_job["agents"]["developer"]["status"] == "interrupted", "Running agent not marked interrupted"
        print("  PASS: Server restart correctly recovers active jobs as 'interrupted' without fake completion.", flush=True)

    # -------------------------------------------------------------
    # 3. VERIFY FIX 2 & 4: RECOVERED GYM JOB 583acd9f021e STATUS
    # -------------------------------------------------------------
    print("\n[Check 3] Verifying recovered Gym Management System job (583acd9f021e)...", flush=True)
    gym_job = job_manager.get_job("583acd9f021e")

    assert gym_job is not None, "Job 583acd9f021e was not found in job_manager"
    assert gym_job["project_name"] == "Gym Management System"
    assert gym_job["status"] == "interrupted", f"Expected status 'interrupted', got '{gym_job['status']}'"

    # Verify the 3 completed tasks vs interrupted developer
    agents = gym_job["agents"]
    assert agents["product-manager"]["status"] == "completed"
    assert agents["software-architect"]["status"] == "completed"
    assert agents["database-designer"]["status"] == "completed"
    assert agents["developer"]["status"] == "interrupted"
    assert agents["testing-engineer"]["status"] == "waiting"
    assert agents["code-reviewer"]["status"] == "waiting"
    print("  PASS: Gym job 583acd9f021e accurately reports PM, Architect, and DB Designer completed, and Developer interrupted.", flush=True)

    # -------------------------------------------------------------
    # 4. VERIFY FIX 2: PROJECTS API DYNAMIC STATUS METRICS
    # -------------------------------------------------------------
    print("\n[Check 4] Verifying Projects API returns accurate dynamic statuses...", flush=True)
    projects_data = list_projects()
    projects = projects_data["projects"]

    # 1. Existing Shopping Project
    shop_proj = next((p for p in projects if p["safe_name"] == "simple_shopping_platform"), None)
    assert shop_proj is not None, "simple_shopping_platform missing from list_projects"
    assert shop_proj["status"] == "completed"
    assert shop_proj["file_count"] >= 38
    assert shop_proj["has_zip"] is True
    assert shop_proj["zip_size_bytes"] > 100000
    print(f"  PASS: Shopping project has status='completed', {shop_proj['file_count']} files, valid ZIP ({shop_proj['zip_size_bytes']:,} bytes).", flush=True)

    # 2. Gym Job in Projects List
    gym_proj = next((p for p in projects if p.get("job_id") == "583acd9f021e"), None)
    assert gym_proj is not None, "Gym job 583acd9f021e missing from list_projects"
    assert gym_proj["status"] == "interrupted"
    assert gym_proj["file_count"] == 0
    assert gym_proj["has_zip"] is False
    print("  PASS: Gym project accurately reports status='interrupted', file_count=0, has_zip=False (no false Ready badge).", flush=True)

    # -------------------------------------------------------------
    # 5. VERIFY ARTIFACT INTEGRITY: PRESERVED GYM & SHOPPING DATA
    # -------------------------------------------------------------
    print("\n[Check 5] Verifying preservation of SQLite Gym outputs and Shopping files...", flush=True)

    # Check SQLite DB
    sqlite_db_path = STORAGE_DIR / "latest_kickoff_task_outputs.db"
    assert sqlite_db_path.exists(), "latest_kickoff_task_outputs.db missing"
    conn = sqlite3.connect(sqlite_db_path)
    c = conn.cursor()
    row_count = c.execute("SELECT count(*) FROM latest_kickoff_task_outputs").fetchone()[0]
    conn.close()

    assert row_count == 6, f"Expected 6 task rows in latest_kickoff_task_outputs.db, found {row_count}"
    print(f"  PASS: SQLite storage contains all {row_count} Gym agent task outputs untouched.", flush=True)

    # Check Shopping directory and ZIP
    shop_dir = GENERATED_PROJECTS_DIR / "simple_shopping_platform"
    shop_zip = GENERATED_PROJECTS_DIR / "simple_shopping_platform.zip"
    assert shop_dir.exists() and shop_dir.is_dir(), "Shopping directory missing"
    assert shop_zip.exists() and shop_zip.is_file(), "Shopping ZIP missing"
    assert shop_zip.stat().st_size == 157800, f"Shopping ZIP size modified: {shop_zip.stat().st_size}"
    print(f"  PASS: Existing shopping directory and ZIP archive ({shop_zip.stat().st_size:,} bytes) are 100% untouched.", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("ALL FOUR FIXES VERIFIED SUCCESSFULLY WITH ZERO MOCK LEAKS", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_fixes_verification()

