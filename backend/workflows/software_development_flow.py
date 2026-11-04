import os
from pathlib import Path
from pydantic import BaseModel, Field
from crewai import Crew, Process
from crewai.flow.flow import Flow, start, listen

from agents.product_manager import create_product_manager
from agents.software_architect import create_software_architect
from agents.database_designer import create_database_designer
from agents.developer import create_developer
from agents.testing_engineer import create_testing_engineer
from agents.code_reviewer import create_code_reviewer

from tasks.development_tasks import create_development_tasks
from services.llm_service import get_llm
from services.project_writer import (
    write_project_files,
    sanitize_project_name,
    validate_project,
    GENERATED_PROJECTS_DIR,
)


def _sanitize_error(message: str) -> str:
    """Ensure sensitive credentials are never exposed in error messages."""
    api_key = os.getenv("META_API_KEY")
    if api_key and len(api_key) > 4 and api_key in message:
        message = message.replace(api_key, "[REDACTED_API_KEY]")
    return message


def _extract_task_output(task) -> str:
    """Extract raw string content from a CrewAI task output object."""
    if hasattr(task, "output") and task.output is not None:
        return getattr(task.output, "raw", str(task.output)).strip()
    return ""


def create_development_crew(llm=None) -> Crew:
    """
    Build and return the assembled six-agent Crew using sequential processing.

    Reuses:
    - get_llm()
    - All six agent factory functions
    - create_development_tasks()
    """
    if llm is None:
        llm = get_llm()

    product_manager = create_product_manager(llm=llm)
    software_architect = create_software_architect(llm=llm)
    database_designer = create_database_designer(llm=llm)
    developer = create_developer(llm=llm)
    testing_engineer = create_testing_engineer(llm=llm)
    code_reviewer = create_code_reviewer(llm=llm)

    tasks = create_development_tasks(
        product_manager=product_manager,
        software_architect=software_architect,
        database_designer=database_designer,
        developer=developer,
        testing_engineer=testing_engineer,
        code_reviewer=code_reviewer,
    )

    crew = Crew(
        agents=[
            product_manager,
            software_architect,
            database_designer,
            developer,
            testing_engineer,
            code_reviewer,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    return crew


# Alias for convenience
build_development_crew = create_development_crew


# Shared workflow state
class DevelopmentState(BaseModel):
    user_requirement: str = ""
    project_name: str = "generated_app"
    task_count: int = 0
    status: str = "not_started"
    execute_crew: bool = True

    # Captured outputs for all six tasks
    requirements_spec: str = ""
    architecture_doc: str = ""
    database_design: str = ""
    developer_output: str = ""
    testing_report: str = ""
    code_review_report: str = ""

    # Project artifacts and files
    project_dir: str = ""
    generated_files: list[str] = Field(default_factory=list)
    error_message: str = ""


class SoftwareDevelopmentFlow(Flow[DevelopmentState]):

    # Step 1: Receive the user's requirement and project name
    @start()
    def receive_requirement(self):
        print("\n==================================================")
        print("DEVTEAM AI - WORKFLOW STARTED")
        print("==================================================")
        print(f"Project Name : {self.state.project_name}")
        print(f"Requirement  : {self.state.user_requirement}")

        return self.state.user_requirement

    # Step 2: Initialize and assemble all six agents and tasks into a Crew
    @listen(receive_requirement)
    def prepare_agent_workflow(self, requirement: str):
        print("\n[Step 1/2] Assembling six development agents and tasks...")

        try:
            self.crew = create_development_crew()
            self.state.task_count = len(self.crew.tasks)
            self.state.status = "ready"

            print(f"All agents initialized. Total tasks: {self.state.task_count}")

            return {
                "requirement": requirement,
                "project_name": self.state.project_name,
                "task_count": self.state.task_count,
                "status": self.state.status,
            }
        except Exception as e:
            err = _sanitize_error(str(e))
            self.state.status = "failed"
            self.state.error_message = err
            print(f"[ERROR] Failed to assemble crew: {err}")
            raise

    # Step 3: Execute the assembled crew when explicitly started and persist outputs
    @listen(prepare_agent_workflow)
    def execute_agent_workflow(self, prep_result: dict):
        if not self.state.execute_crew:
            print("\n[INFO] Workflow prepared in readiness mode (execute_crew is False).")
            return prep_result

        print("\n[Step 2/2] Executing six-agent sequential crew...")
        self.state.status = "running"

        try:
            # 1. Execute the assembled crew
            self.crew.kickoff(
                inputs={"user_requirement": self.state.user_requirement}
            )

            # 2. Capture all six task outputs in workflow state
            tasks = self.crew.tasks
            if len(tasks) >= 6:
                self.state.requirements_spec = _extract_task_output(tasks[0])
                self.state.architecture_doc = _extract_task_output(tasks[1])
                self.state.database_design = _extract_task_output(tasks[2])
                self.state.developer_output = _extract_task_output(tasks[3])
                self.state.testing_report = _extract_task_output(tasks[4])
                self.state.code_review_report = _extract_task_output(tasks[5])

            # 3. Save developer output to generated_projects/ via project_writer
            project_name = self.state.project_name or "generated_app"
            safe_name = sanitize_project_name(project_name)

            # Avoid folder collision if a project with the same name exists
            candidate_name = project_name
            counter = 1
            while (GENERATED_PROJECTS_DIR / safe_name).exists():
                candidate_name = f"{project_name}_{counter}"
                safe_name = sanitize_project_name(candidate_name)
                counter += 1

            written_files = write_project_files(
                developer_output=self.state.developer_output,
                project_name=candidate_name,
            )

            project_dir = GENERATED_PROJECTS_DIR / safe_name
            self.state.project_dir = str(project_dir)

            # 4. Save testing and code-review reports in the project directory
            if self.state.testing_report:
                test_report_file = project_dir / "TEST_REPORT.md"
                test_report_file.write_text(self.state.testing_report, encoding="utf-8")
                written_files.append("TEST_REPORT.md")

            if self.state.code_review_report:
                review_report_file = project_dir / "CODE_REVIEW.md"
                review_report_file.write_text(self.state.code_review_report, encoding="utf-8")
                written_files.append("CODE_REVIEW.md")

            # Save requirements and architecture documents for full traceability
            if self.state.requirements_spec:
                req_file = project_dir / "REQUIREMENTS.md"
                req_file.write_text(self.state.requirements_spec, encoding="utf-8")
                written_files.append("REQUIREMENTS.md")

            if self.state.architecture_doc:
                arch_file = project_dir / "ARCHITECTURE.md"
                arch_file.write_text(self.state.architecture_doc, encoding="utf-8")
                written_files.append("ARCHITECTURE.md")

            self.state.generated_files = written_files

            # Quality gate: Validate project syntax and completeness
            validation_result = validate_project(project_dir)
            if validation_result["has_critical_errors"]:
                error_summary = "; ".join(validation_result["errors"][:3])
                self.state.status = "incomplete"
                self.state.error_message = f"Quality gate validation failed: {error_summary}"
                print(f"\n[WARNING] Quality gate failed with {len(validation_result['errors'])} critical errors.")
                return {
                    "project_name": candidate_name,
                    "project_dir": str(project_dir),
                    "generated_files": written_files,
                    "status": "incomplete",
                    "validation_errors": validation_result["errors"],
                }

            self.state.status = "completed"

            print("\n==================================================")
            print("DEVTEAM AI - WORKFLOW COMPLETED SUCCESSFULLY")
            print("==================================================")
            print(f"Project Directory : {project_dir}")
            print(f"Files Generated   : {len(written_files)}")
            for f in written_files:
                print(f"  - {f}")

            return {
                "project_name": candidate_name,
                "project_dir": str(project_dir),
                "generated_files": written_files,
                "status": "completed",
            }

        except Exception as e:
            err = _sanitize_error(str(e))
            self.state.status = "failed"
            self.state.error_message = err
            print(f"\n[ERROR] Workflow execution failed: {err}")
            raise RuntimeError(err) from None
