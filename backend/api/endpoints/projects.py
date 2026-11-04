import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.job_manager import (
    GENERATED_PROJECTS_DIR,
    build_file_tree,
    job_manager,
)
from services.project_writer import sanitize_project_name

router = APIRouter()


class GenerateProjectRequest(BaseModel):
    projectName: Optional[str] = None
    project_name: Optional[str] = None
    requirement: str

    class Config:
        populate_by_name = True


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_project(payload: GenerateProjectRequest):
    """
    Start the multi-agent software generation workflow in the background.
    Returns a unique job ID immediately without blocking the request.
    """
    name = payload.projectName or payload.project_name
    if not name or len(name.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name must be at least 3 characters long.",
        )

    requirement = payload.requirement.strip()
    if not requirement or len(requirement) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirement description must be at least 10 characters long.",
        )

    # Initialize job in job manager
    job = job_manager.create_job(project_name=name, requirement=requirement)

    # Launch background worker
    job_manager.start_job(job["job_id"])

    return {
        "job_id": job["job_id"],
        "project_name": job["project_name"],
        "safe_project_name": job["safe_project_name"],
        "status": job["status"],
        "message": "Project generation initiated in background worker.",
    }


@router.get("/status/{job_id}")
@router.get("/{job_id}/status")
def get_job_status(job_id: str):
    """
    Retrieve real-time progress, agent statuses, and activity for a generation job.
    Designed for 2-second client polling.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    return job


@router.get("/files/{job_id_or_name}")
@router.get("/{job_id_or_name}/files")
def get_project_files(job_id_or_name: str):
    """
    Retrieve the generated file tree structure formatted for the React FileExplorer.
    Accepts either a job ID or a project name.
    """
    project_dir = None
    display_name = job_id_or_name

    # 1. Try finding by active/recent job ID
    job = job_manager.get_job(job_id_or_name)
    if job and job.get("project_dir"):
        p_dir = Path(job["project_dir"])
        if p_dir.exists():
            project_dir = p_dir
            display_name = job["project_name"]

    # 2. Try finding by project name on disk
    if project_dir is None:
        try:
            safe_name = sanitize_project_name(job_id_or_name)
            candidate = (GENERATED_PROJECTS_DIR / safe_name).resolve()

            # Security check: Ensure candidate path does not escape generated_projects dir
            candidate.relative_to(GENERATED_PROJECTS_DIR.resolve())

            if candidate.exists() and candidate.is_dir():
                project_dir = candidate
                display_name = safe_name
        except Exception:
            pass

    if project_dir is None or not project_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No generated project files found for '{job_id_or_name}'.",
        )

    # Scan project files on disk
    rel_files = []
    for file_path in project_dir.rglob("*"):
        if file_path.is_file():
            rel_files.append(file_path.relative_to(project_dir).as_posix())

    file_tree = build_file_tree(rel_files)

    return {
        "project_name": display_name,
        "files": file_tree,
        "total_files": len(rel_files),
    }


@router.get("/download/{job_id_or_name}")
@router.get("/{job_id_or_name}/download")
def download_project_zip(job_id_or_name: str):
    """
    Download the generated project ZIP archive.
    Accepts either a job ID or a project name.
    """
    zip_path = None
    filename = f"{job_id_or_name}.zip"

    # 1. Try finding by job ID
    job = job_manager.get_job(job_id_or_name)
    if job and job.get("zip_path"):
        zp = Path(job["zip_path"])
        if zp.exists() and zp.is_file():
            zip_path = zp
            filename = f"{job['safe_project_name']}.zip"

    # 2. Try finding by project name on disk
    if zip_path is None:
        try:
            safe_name = sanitize_project_name(job_id_or_name)
            candidate = (GENERATED_PROJECTS_DIR / f"{safe_name}.zip").resolve()

            # Security check: Ensure candidate path does not escape generated_projects dir
            candidate.relative_to(GENERATED_PROJECTS_DIR.resolve())

            if candidate.exists() and candidate.is_file():
                zip_path = candidate
                filename = f"{safe_name}.zip"
        except Exception:
            pass

    if zip_path is None or not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ZIP archive not found for '{job_id_or_name}'.",
        )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=filename,
    )


@router.get("")
def list_projects():
    """
    List all generated projects available on disk, merged with persistent job registry.
    """
    projects = []
    seen_safe_names = set()

    # 1. First add all tracked jobs from the persistent job registry
    for job in job_manager.list_jobs():
        safe_name = job["safe_project_name"]
        seen_safe_names.add(safe_name)

        proj_dir = Path(job.get("project_dir", GENERATED_PROJECTS_DIR / safe_name))
        on_disk_files = [f for f in proj_dir.rglob("*") if f.is_file()] if proj_dir.exists() else []
        file_count = len(on_disk_files) if on_disk_files else len(job.get("generated_files", []))

        zip_file = Path(job.get("zip_path", GENERATED_PROJECTS_DIR / f"{safe_name}.zip"))
        has_zip = zip_file.exists() and zip_file.is_file()

        projects.append({
            "job_id": job["job_id"],
            "name": job["project_name"],
            "safe_name": safe_name,
            "status": job["status"],
            "file_count": file_count,
            "has_zip": has_zip,
            "zip_size_bytes": zip_file.stat().st_size if has_zip else 0,
            "progress": job.get("progress", 0),
            "error_message": job.get("error_message"),
            "activity": job.get("activity"),
        })

    # 2. Add any standalone project folders on disk not created via tracked jobs (e.g. simple_shopping_platform)
    if GENERATED_PROJECTS_DIR.exists():
        for item in sorted(GENERATED_PROJECTS_DIR.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                name = item.name
                if name not in seen_safe_names:
                    seen_safe_names.add(name)
                    files = [f for f in item.rglob("*") if f.is_file()]
                    zip_file = GENERATED_PROJECTS_DIR / f"{name}.zip"
                    has_zip = zip_file.exists() and zip_file.is_file()

                    # Status is completed ONLY if it has real files and a valid ZIP
                    status_val = "completed" if (len(files) > 0 and has_zip) else "incomplete"

                    projects.append({
                        "name": name,
                        "safe_name": name,
                        "status": status_val,
                        "file_count": len(files),
                        "has_zip": has_zip,
                        "zip_size_bytes": zip_file.stat().st_size if has_zip else 0,
                        "path": str(item),
                    })

    return {
        "projects": projects,
        "total": len(projects),
    }
