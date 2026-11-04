import os
import sys
import time
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException
from fastapi.responses import FileResponse
from api.endpoints.projects import (
    GenerateProjectRequest,
    generate_project,
    get_job_status,
    get_project_files,
    download_project_zip,
    list_projects,
)
from services.job_manager import AGENT_ORDER, JobManager, job_manager


def run_tests():
    print("=" * 70, flush=True)
    print("RUNNING DEVTEAM AI BACKEND DIRECT INTEGRATION TESTS", flush=True)
    print("=" * 70, flush=True)

    # 1. Validation tests
    print("\n[Test 1] Testing input validation on generate_project...", flush=True)

    # Short project name (< 3 chars)
    try:
        generate_project(GenerateProjectRequest(projectName="ab", requirement="A valid requirement."))
        raise AssertionError("Expected HTTPException for short project name")
    except HTTPException as e:
        assert e.status_code == 400
        print("  PASS: Rejects short project name (< 3 chars).", flush=True)

    # Short requirement (< 10 chars)
    try:
        generate_project(GenerateProjectRequest(projectName="Gym App", requirement="Short"))
        raise AssertionError("Expected HTTPException for short requirement")
    except HTTPException as e:
        assert e.status_code == 400
        print("  PASS: Rejects short requirement (< 10 chars).", flush=True)

    # Non-existent job status
    try:
        get_job_status("nonexistent_id_999")
        raise AssertionError("Expected HTTPException for unknown job ID")
    except HTTPException as e:
        assert e.status_code == 404
        print("  PASS: Returns 404 for unknown job ID.", flush=True)

    # 2. State Machine & Event Tracking
    print("\n[Test 2] Testing real execution tracking state machine...", flush=True)
    test_mgr = JobManager()
    job = test_mgr.create_job("Gym Management Platform", "Build a gym membership and class scheduling platform.")
    job_id = job["job_id"]

    assert job["status"] == "queued"
    assert len(job["agents"]) == 6
    assert all(a["status"] == "waiting" for a in job["agents"].values())
    print("  PASS: Job initialized as queued with all 6 agents waiting.", flush=True)

    # Transition Agent 1 to running
    test_mgr.update_job(job_id, status="running", progress=10, activity="Product Manager analyzing requirements...")
    test_mgr.update_agent(job_id, "product-manager", status="running", progress=20, activity="Drafting SRS...")

    j = test_mgr.get_job(job_id)
    assert j["status"] == "running"
    assert j["agents"]["product-manager"]["status"] == "running"
    assert j["agents"]["software-architect"]["status"] == "waiting"
    print("  PASS: Agent 1 running; other agents remain in waiting state.", flush=True)

    # Transition Agent 1 to completed, Agent 2 to running
    test_mgr.update_agent(job_id, "product-manager", status="completed", progress=100, activity="SRS complete.")
    test_mgr.update_agent(job_id, "software-architect", status="running", progress=15, activity="Designing system architecture...")
    test_mgr.update_job(job_id, current_agent="software-architect", current_task=2, progress=25)

    j = test_mgr.get_job(job_id)
    assert j["agents"]["product-manager"]["status"] == "completed"
    assert j["agents"]["software-architect"]["status"] == "running"
    assert j["agents"]["database-designer"]["status"] == "waiting"
    print("  PASS: Agent 1 completed; Agent 2 transitioned to running.", flush=True)

    # Test error handling
    test_mgr.update_agent(job_id, "software-architect", status="error", activity="Failed: LLM rate limit reached.")
    test_mgr.update_job(job_id, status="failed", error_message="LLM rate limit reached.")

    j = test_mgr.get_job(job_id)
    assert j["status"] == "failed"
    assert j["agents"]["software-architect"]["status"] == "error"
    assert "rate limit" in j["error_message"].lower()
    print("  PASS: Failure captured accurately across job and active agent.", flush=True)

    # 3. Existing Project Queries & File Tree
    print("\n[Test 3] Testing existing project queries (simple_shopping_platform)...", flush=True)

    # List projects
    projects_list = list_projects()
    assert projects_list["total"] >= 1
    proj_names = [p["safe_name"] for p in projects_list["projects"]]
    assert "simple_shopping_platform" in proj_names
    print(f"  PASS: list_projects returned {projects_list['total']} project(s): {proj_names}", flush=True)

    # Get file tree
    files_res = get_project_files("simple_shopping_platform")
    assert files_res["total_files"] >= 38
    assert len(files_res["files"]) > 0

    # Verify nested file tree structure
    top_level_names = [node["name"] for node in files_res["files"]]
    assert "backend" in top_level_names
    assert "frontend" in top_level_names
    assert "database" in top_level_names
    print(f"  PASS: get_project_files returned valid tree with {files_res['total_files']} files.", flush=True)

    # Get ZIP download
    dl_res = download_project_zip("simple_shopping_platform")
    assert isinstance(dl_res, FileResponse)
    assert Path(dl_res.path).exists()
    assert dl_res.media_type == "application/zip"
    assert "simple_shopping_platform.zip" in dl_res.filename
    print(f"  PASS: download_project_zip returned FileResponse pointing to {dl_res.filename}.", flush=True)

    # Test path traversal defense
    try:
        get_project_files("../../outside")
        raise AssertionError("Expected 404 for path traversal in get_project_files")
    except HTTPException as e:
        assert e.status_code == 404
        print("  PASS: Path traversal rejected in get_project_files.", flush=True)

    try:
        download_project_zip("../../secret")
        raise AssertionError("Expected 404 for path traversal in download_project_zip")
    except HTTPException as e:
        assert e.status_code == 404
        print("  PASS: Path traversal rejected in download_project_zip.", flush=True)

    # 4. Background Job Generation & Polling Flow (Mock worker, no Meta API)
    print("\n[Test 4] Testing end-to-end background generation & polling flow...", flush=True)

    def mock_worker(j_id: str):
        for idx, agent in enumerate(AGENT_ORDER):
            job_manager.update_agent(j_id, agent["id"], status="running", progress=20, activity=f"{agent['name']} working...")
            job_manager.update_job(j_id, status="running", current_agent=agent["id"], current_task=idx + 1, progress=int((idx + 1) / 6 * 90))
            time.sleep(0.04)
            job_manager.update_agent(j_id, agent["id"], status="completed", progress=100, activity=f"{agent['name']} finished.")

        job_manager.update_job(
            j_id,
            status="completed",
            progress=100,
            activity="Build complete.",
            generated_files=["backend/app/main.py", "frontend/App.jsx", "README.md"],
        )

    # Intercept worker for testing
    orig_start = job_manager.start_job
    try:
        job_manager.start_job = lambda j_id: orig_start(j_id, worker_fn=mock_worker)

        gen_res = generate_project(
            GenerateProjectRequest(
                projectName="Gym Management Website",
                requirement="Build a complete gym management platform with classes, trainers, and online bookings.",
            )
        )

        test_job_id = gen_res["job_id"]
        assert gen_res["status"] == "queued"
        print(f"  PASS: generate_project accepted job '{test_job_id}'.", flush=True)

        # Poll status until complete
        completed = False
        for _ in range(30):
            st = get_job_status(test_job_id)
            if st["status"] == "completed":
                completed = True
                assert st["progress"] == 100
                assert all(ag["status"] == "completed" for ag in st["agents"].values())
                break
            time.sleep(0.05)

        assert completed, "Background worker did not complete in time."
        print(f"  PASS: Polled get_job_status to completion. All 6 agents completed (progress: 100%).", flush=True)

    finally:
        job_manager.start_job = orig_start

    print("\n" + "=" * 70, flush=True)
    print("ALL DEVTEAM AI BACKEND DIRECT INTEGRATION TESTS PASSED!", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_tests()
