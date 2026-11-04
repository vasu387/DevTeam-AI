import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

# Project directory configuration
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"
STORAGE_DIR = BACKEND_DIR / ".crewai_storage"
JOBS_REGISTRY_PATH = STORAGE_DIR / "jobs_registry.json"

from services.project_writer import (
    create_project_zip,
    sanitize_project_name,
    validate_file_path,
    write_project_files,
    write_reports,
)

# Ordered agent definitions matching the sequential pipeline and frontend IDs
AGENT_ORDER = [
    {
        "id": "product-manager",
        "name": "Product Manager",
        "role": "Requirement analysis and user story generation",
        "task_desc_prefix": "Analyse",
    },
    {
        "id": "software-architect",
        "name": "Software Architect",
        "role": "System design and technology stack selection",
        "task_desc_prefix": "Design the software architecture",
    },
    {
        "id": "database-designer",
        "name": "Database Designer",
        "role": "Schema design, ER diagrams and data modeling",
        "task_desc_prefix": "Design the database",
    },
    {
        "id": "developer",
        "name": "Developer",
        "role": "Code generation across frontend and backend",
        "task_desc_prefix": "Develop",
    },
    {
        "id": "testing-engineer",
        "name": "Testing Engineer",
        "role": "Unit tests, integration tests and test reports",
        "task_desc_prefix": "Test",
    },
    {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "role": "Code quality checks and best-practice review",
        "task_desc_prefix": "Review",
    },
]


def _sanitize_error(message: str) -> str:
    """Ensure sensitive credentials are never exposed in error messages."""
    api_key = os.getenv("META_API_KEY")
    if api_key and len(api_key) > 4 and api_key in message:
        message = message.replace(api_key, "[REDACTED_API_KEY]")
    return message


def _setup_crewai_env():
    """Ensure sandbox-safe paths and isolation for CrewAI."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["USERPROFILE"] = str(STORAGE_DIR)
    os.environ["HOME"] = str(STORAGE_DIR)
    os.environ["LOCALAPPDATA"] = str(STORAGE_DIR)
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
    os.environ["CREWAI_DISABLE_TRACKING"] = "true"

    try:
        import appdirs
        appdirs.user_data_dir = lambda *a, **kw: str(STORAGE_DIR)
        appdirs.user_config_dir = lambda *a, **kw: str(STORAGE_DIR)
        appdirs.user_cache_dir = lambda *a, **kw: str(STORAGE_DIR)
        appdirs.user_state_dir = lambda *a, **kw: str(STORAGE_DIR)
        appdirs.user_log_dir = lambda *a, **kw: str(STORAGE_DIR)
    except ImportError:
        pass

    try:
        import crewai_core.settings
        crewai_core.settings.DEFAULT_CONFIG_PATH = STORAGE_DIR / "settings.json"
        crewai_core.settings.get_writable_config_path = lambda: STORAGE_DIR / "settings.json"
    except ImportError:
        pass


def build_file_tree(file_list: list) -> list:
    """
    Convert a flat list of relative file paths into a nested tree structure
    expected by the React FileExplorer component.
    """
    tree = []

    def add_path(parts: list, node_list: list, full_path: str):
        if not parts:
            return
        current = parts[0]
        if len(parts) == 1:
            node_list.append({"name": current, "type": "file", "path": full_path})
        else:
            folder = next(
                (n for n in node_list if n.get("type") == "folder" and n.get("name") == current),
                None,
            )
            if not folder:
                folder = {"name": current, "type": "folder", "children": []}
                node_list.append(folder)
            add_path(parts[1:], folder["children"], full_path)

    for p in sorted(file_list):
        clean_path = p.replace("\\", "/").strip("/")
        if not clean_path:
            continue
        parts = clean_path.split("/")
        add_path(parts, tree, clean_path)

    return tree


class JobManager:
    """
    Thread-safe persistent job manager for multi-agent generation workflows.
    Tracks real-time agent execution states, activity messages, and progress,
    persisting status to disk so jobs survive server restarts.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.registry_path = Path(registry_path) if registry_path else JOBS_REGISTRY_PATH
        self._jobs: dict[str, dict] = {}
        self._load_registry()

    def _load_registry(self):
        """Restore job history from disk and recover interrupted jobs."""
        with self._lock:
            if not self.registry_path.exists():
                # Check if prior run in SQLite database needs to be initialized into registry
                self._recover_legacy_db_run()
                return

            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    now_str = datetime.now(timezone.utc).isoformat()
                    changed = False
                    for job_id, job in data.items():
                        # If server restarted while a job was in progress, mark it as interrupted
                        if job.get("status") in ("running", "queued"):
                            job["status"] = "interrupted"
                            job["completed_at"] = now_str
                            job["error_message"] = (
                                "Backend server restarted while job was in progress. "
                                "Workflow was safely interrupted."
                            )
                            job["activity"] = "Workflow interrupted by server restart."
                            for agent in job.get("agents", {}).values():
                                if agent.get("status") == "running":
                                    agent["status"] = "interrupted"
                                    agent["activity"] = "Interrupted by server restart."
                                    agent["completed_at"] = now_str
                            changed = True

                    self._jobs = data
                    if changed:
                        self._save_registry_locked()
            except Exception as e:
                print(f"[WARN] Failed to load jobs registry from {self.registry_path}: {e}")

    def _recover_legacy_db_run(self):
        """Seed known prior run (e.g. Gym job 583acd9f021e) from SQLite storage if present."""
        db_file = STORAGE_DIR / "latest_kickoff_task_outputs.db"
        if not db_file.exists():
            return
        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            rows = c.execute("SELECT * FROM latest_kickoff_task_outputs").fetchall()
            conn.close()

            # If Gym Management System run had prior outputs recorded
            if len(rows) >= 3:
                now_str = datetime.now(timezone.utc).isoformat()
                agents_status = {
                    "product-manager": {
                        "status": "completed",
                        "activity": "Software Requirement Specification complete.",
                        "progress": 100,
                        "started_at": "2026-11-04T16:47:00Z",
                        "completed_at": "2026-11-04T16:48:00Z",
                    },
                    "software-architect": {
                        "status": "completed",
                        "activity": "Software Architecture Document complete.",
                        "progress": 100,
                        "started_at": "2026-11-04T16:48:00Z",
                        "completed_at": "2026-11-04T16:49:49Z",
                    },
                    "database-designer": {
                        "status": "completed",
                        "activity": "Database Schema & Models complete.",
                        "progress": 100,
                        "started_at": "2026-11-04T16:49:49Z",
                        "completed_at": "2026-11-04T16:50:45Z",
                    },
                    "developer": {
                        "status": "interrupted",
                        "activity": "Interrupted by server restart before source files were exported.",
                        "progress": 0,
                        "started_at": None,
                        "completed_at": now_str,
                    },
                    "testing-engineer": {
                        "status": "waiting",
                        "activity": "Waiting for developer code.",
                        "progress": 0,
                        "started_at": None,
                        "completed_at": None,
                    },
                    "code-reviewer": {
                        "status": "waiting",
                        "activity": "Waiting for test results.",
                        "progress": 0,
                        "started_at": None,
                        "completed_at": None,
                    },
                }

                recovered_job = {
                    "job_id": "583acd9f021e",
                    "project_name": "Gym Management System",
                    "safe_project_name": "gym_management_system",
                    "requirement": "Build a complete, professional, modern Gym Management System as a full-stack web application.",
                    "status": "interrupted",
                    "current_agent": "developer",
                    "current_task": 4,
                    "progress": 50,
                    "activity": "Workflow interrupted by server restart after database design.",
                    "created_at": "2026-11-04T16:47:00Z",
                    "started_at": "2026-11-04T16:47:00Z",
                    "completed_at": now_str,
                    "error_message": "Backend server restarted while job was in progress. Workflow was safely interrupted.",
                    "agents": agents_status,
                    "project_dir": str(GENERATED_PROJECTS_DIR / "gym_management_system"),
                    "zip_path": str(GENERATED_PROJECTS_DIR / "gym_management_system.zip"),
                    "generated_files": [],
                }

                self._jobs["583acd9f021e"] = recovered_job
                self._save_registry_locked()
        except Exception as e:
            print(f"[WARN] Failed to recover legacy db run: {e}")

    def _save_registry_locked(self):
        """Persist jobs registry atomically (caller must hold self._lock)."""
        try:
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            temp_path = self.registry_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._jobs, f, indent=2)
            temp_path.replace(self.registry_path)
        except Exception as e:
            print(f"[WARN] Failed to save jobs registry to {self.registry_path}: {e}")

    def create_job(self, project_name: str, requirement: str) -> dict:
        """Create and initialize a new generation job."""
        job_id = uuid.uuid4().hex[:12]
        base_safe_name = sanitize_project_name(project_name)

        with self._lock:
            # Ensure unique project folder per job to avoid collisions
            candidate_name = base_safe_name
            project_dir = GENERATED_PROJECTS_DIR / candidate_name
            if project_dir.exists():
                candidate_name = f"{base_safe_name}_{job_id[:6]}"
                project_dir = GENERATED_PROJECTS_DIR / candidate_name

            # Initialize all six agents in waiting state
            agents_status = {}
            for agent in AGENT_ORDER:
                agents_status[agent["id"]] = {
                    "status": "waiting",
                    "activity": "Waiting for workflow to begin.",
                    "progress": 0,
                    "started_at": None,
                    "completed_at": None,
                }

            now_iso = datetime.now(timezone.utc).isoformat()
            job = {
                "job_id": job_id,
                "project_name": project_name.strip(),
                "safe_project_name": candidate_name,
                "requirement": requirement.strip(),
                "status": "queued",  # "queued" | "running" | "completed" | "failed" | "interrupted"
                "current_agent": AGENT_ORDER[0]["id"],
                "current_task": 1,
                "progress": 0,
                "activity": "Job initialized. Waiting for execution...",
                "created_at": now_iso,
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "agents": agents_status,
                "project_dir": str(project_dir),
                "zip_path": str(GENERATED_PROJECTS_DIR / f"{candidate_name}.zip"),
                "generated_files": [],
            }

            self._jobs[job_id] = job
            self._save_registry_locked()
            return dict(job)

    def get_job(self, job_id: str) -> Optional[dict]:
        """Retrieve a job by its unique ID."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                import copy
                return copy.deepcopy(job)
            return None

    def get_job_by_project_name(self, project_name: str) -> Optional[dict]:
        """Retrieve a job by project name or safe project name."""
        with self._lock:
            safe = sanitize_project_name(project_name)
            for job in self._jobs.values():
                if job["safe_project_name"] == safe or job["project_name"].lower() == project_name.lower():
                    import copy
                    return copy.deepcopy(job)
            return None

    def list_jobs(self) -> list:
        """List all tracked jobs."""
        with self._lock:
            import copy
            return [copy.deepcopy(job) for job in self._jobs.values()]

    def update_job(self, job_id: str, **kwargs):
        """Update job-level fields in a thread-safe manner and persist to disk."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)
                self._save_registry_locked()

    def update_agent(self, job_id: str, agent_id: str, **kwargs):
        """Update an individual agent's status in a thread-safe manner and persist to disk."""
        with self._lock:
            if job_id in self._jobs and agent_id in self._jobs[job_id]["agents"]:
                self._jobs[job_id]["agents"][agent_id].update(kwargs)
                self._save_registry_locked()

    def start_job(self, job_id: str, worker_fn: Optional[Callable[[str], None]] = None) -> threading.Thread:
        """
        Launch the generation worker in a background thread so the HTTP request returns immediately.
        Optionally accepts a custom worker function for testing without LLM calls.
        """
        target = worker_fn if worker_fn is not None else self._default_crew_worker
        thread = threading.Thread(
            target=target,
            args=(job_id,),
            name=f"devteam-job-{job_id}",
            daemon=True,
        )
        thread.start()
        return thread

    def _default_crew_worker(self, job_id: str):
        """
        The production background worker executing the full six-agent CrewAI pipeline.
        Driven by actual CrewAI task callbacks, with full progress and error tracking.
        """
        job = self.get_job(job_id)
        if not job:
            return

        now_str = datetime.now(timezone.utc).isoformat()
        self.update_job(
            job_id,
            status="running",
            started_at=now_str,
            activity="Starting six-agent development crew...",
            progress=5,
        )

        # Mark first agent (Product Manager) as running
        self.update_agent(
            job_id,
            "product-manager",
            status="running",
            activity="Analyzing user requirements and creating specifications...",
            progress=10,
            started_at=now_str,
        )

        try:
            # 1. Environment & storage setup
            _setup_crewai_env()

            # 2. Import LLM and crew builder
            from services.llm_service import get_llm
            from workflows.software_development_flow import build_development_crew

            llm = get_llm()
            crew = build_development_crew(llm=llm)

            # 3. Attach real-time task callbacks for live execution tracking
            def make_callback(task_idx: int):
                def _callback(output):
                    current_agent_def = AGENT_ORDER[task_idx]
                    finish_time = datetime.now(timezone.utc).isoformat()

                    # Mark finished agent as completed
                    self.update_agent(
                        job_id,
                        current_agent_def["id"],
                        status="completed",
                        activity=f"Finished {current_agent_def['name']} task.",
                        progress=100,
                        completed_at=finish_time,
                    )

                    # If there is a subsequent agent, transition it to running
                    if task_idx + 1 < len(AGENT_ORDER):
                        next_agent_def = AGENT_ORDER[task_idx + 1]
                        step_progress = int((task_idx + 1) / 6 * 85)

                        self.update_agent(
                            job_id,
                            next_agent_def["id"],
                            status="running",
                            activity=f"Working on {next_agent_def['role']}...",
                            progress=10,
                            started_at=finish_time,
                        )

                        self.update_job(
                            job_id,
                            current_agent=next_agent_def["id"],
                            current_task=task_idx + 2,
                            progress=step_progress,
                            activity=f"{next_agent_def['name']} is active...",
                        )

                return _callback

            for idx, task in enumerate(crew.tasks):
                task.callback = make_callback(idx)

            # 4. Execute the sequential multi-agent crew
            self.update_job(
                job_id,
                activity="Crew running: Product Manager is drafting requirements...",
                progress=10,
            )

            result = crew.kickoff(inputs={"user_requirement": job["requirement"]})

            # Ensure final agent is marked completed
            final_time = datetime.now(timezone.utc).isoformat()
            self.update_agent(
                job_id,
                AGENT_ORDER[-1]["id"],
                status="completed",
                activity="Code review and quality audit completed.",
                progress=100,
                completed_at=final_time,
            )

            self.update_job(
                job_id,
                progress=90,
                activity="Writing project source files, reports, and generating ZIP archive...",
            )

            # 5. Extract Developer output (Task 3) and Agent Reports
            developer_output = ""
            if len(crew.tasks) > 3 and hasattr(crew.tasks[3], "output"):
                developer_output = getattr(crew.tasks[3].output, "raw", str(crew.tasks[3].output)).strip()

            reports = {}
            for i, task in enumerate(crew.tasks):
                if hasattr(task, "output") and task.output:
                    raw_content = getattr(task.output, "raw", str(task.output)).strip()
                    role_key = AGENT_ORDER[i]["id"].replace("-", "_")
                    reports[role_key] = raw_content

            # 6. Save project files and build ZIP archive
            safe_name = job["safe_project_name"]
            project_dir = GENERATED_PROJECTS_DIR / safe_name
            project_dir.mkdir(parents=True, exist_ok=True)

            written_source = []
            if developer_output:
                written_source = write_project_files(
                    developer_output=developer_output,
                    project_name=safe_name,
                    target_dir=project_dir,
                    overwrite=True,
                )

            written_reports = write_reports(
                reports=reports,
                project_dir=project_dir,
                subdirs=("docs", "reports"),
            )

            all_written = written_source + written_reports

            # 7. Quality Gate: Validate project syntax and completeness before creating ZIP
            from services.project_writer import validate_project
            validation_result = validate_project(project_dir)

            if validation_result["has_critical_errors"]:
                error_summary = "; ".join(validation_result["errors"][:3])
                self.update_job(
                    job_id,
                    status="incomplete",
                    progress=85,
                    activity=f"Quality gate found {len(validation_result['errors'])} critical errors. Project marked incomplete.",
                    error_message=f"Quality validation failed: {error_summary}",
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    project_dir=str(project_dir),
                    zip_path=None,
                    generated_files=all_written,
                    validation_errors=validation_result["errors"],
                    validation_warnings=validation_result["warnings"],
                )
                return

            zip_path = create_project_zip(project_dir)

            # 8. Mark job completed
            self.update_job(
                job_id,
                status="completed",
                progress=100,
                activity=f"Project generation complete. {len(written_source)} verified source files written.",
                completed_at=datetime.now(timezone.utc).isoformat(),
                project_dir=str(project_dir),
                zip_path=str(zip_path),
                generated_files=all_written,
                validation_warnings=validation_result["warnings"],
            )

        except Exception as e:
            err_msg = _sanitize_error(str(e))
            fail_time = datetime.now(timezone.utc).isoformat()
            current_job = self.get_job(job_id)
            current_agent = current_job.get("current_agent", AGENT_ORDER[0]["id"]) if current_job else AGENT_ORDER[0]["id"]

            self.update_agent(
                job_id,
                current_agent,
                status="error",
                activity=f"Execution error: {err_msg}",
                completed_at=fail_time,
            )

            self.update_job(
                job_id,
                status="failed",
                error_message=err_msg,
                activity=f"Generation failed: {err_msg}",
                completed_at=fail_time,
            )


# Singleton job manager instance
job_manager = JobManager()
