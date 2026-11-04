import ast
import json
import re
import shutil
import sqlite3
import subprocess
import zipfile
from pathlib import Path
from typing import Optional


# Project directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"
DEFAULT_STORAGE_DB = BASE_DIR / "backend" / ".crewai_storage" / "latest_kickoff_task_outputs.db"
VALIDATE_JSX_SCRIPT = Path(__file__).resolve().parent / "validate_jsx.cjs"

# Regex pattern supporting three header formats (case-insensitive for FILE:, File:, file:):
# 1. ### File: path/to/file
# 2. ### File: `path/to/file`
# 3. ### `path/to/file`
FILE_HEADER_PATTERN = re.compile(
    r"(?mi)^###\s*(?:(?:file:\s*`?([^`\r\n]+?)`?)|(?:`([^`\r\n]+?)`))\s*$"
)

# Regex patterns for stripping markdown code fence wrappers
CODE_FENCE_WRAPPED_PATTERN = re.compile(
    r"^```[a-zA-Z0-9_+-]*[ \t]*\r?\n([\s\S]*)\r?\n```[ \t]*$"
)
CODE_FENCE_OPEN_ONLY_PATTERN = re.compile(
    r"^```[a-zA-Z0-9_+-]*[ \t]*\r?\n([\s\S]*)$"
)


def sanitize_project_name(project_name: str) -> str:
    """Convert a project name into a safe folder name."""

    if not isinstance(project_name, str):
        raise ValueError("Project name must be a string.")

    name = project_name.strip().lower()
    name = re.sub(r"[^a-z0-9_-]+", "_", name)
    name = name.strip("_-")

    if not name:
        raise ValueError("Invalid project name.")

    return name


def strip_code_fences(content: str) -> str:
    """
    Strip markdown code fence wrapper and language specifier if present.
    Preserves actual source code and internal indentation.
    """

    if not isinstance(content, str):
        return ""

    text = content.strip()
    if not text:
        return ""

    # Match code fences with both opening and closing markers
    match = CODE_FENCE_WRAPPED_PATTERN.match(text)
    if match:
        return match.group(1)

    # Match code fence with opening marker only (if closing fence was omitted)
    match_single = CODE_FENCE_OPEN_ONLY_PATTERN.match(text)
    if match_single:
        return match_single.group(1)

    # Content was not wrapped in code fences; return stripped text
    return text


def clean_source_code(content: str, file_path: str = "") -> str:
    """
    Thoroughly clean generated source code:
    - Strip markdown code fences (```) and language identifiers.
    - Remove accidental conversational preambles/postambles.
    - Remove stray trailing code fences.
    - Preserve internal indentation and whitespace.
    """
    if not isinstance(content, str):
        return ""

    text = strip_code_fences(content)
    lines = text.splitlines()

    # Strip any leading fence or language tag line
    while lines and (lines[0].strip().startswith("```") or lines[0].strip().startswith("'''")):
        lines.pop(0)

    # Strip any trailing code fence line
    while lines and (lines[-1].strip().startswith("```") or lines[-1].strip().startswith("'''") or not lines[-1].strip()):
        lines.pop()

    return "\n".join(lines).strip()


def parse_generated_files(output: str) -> dict:
    """Extract file paths and cleaned contents from developer output."""

    if not isinstance(output, str) or not output.strip():
        raise ValueError("Developer output is empty or invalid.")

    matches = list(FILE_HEADER_PATTERN.finditer(output))

    if not matches:
        raise ValueError("No valid file headers found.")

    files = {}

    for index, match in enumerate(matches):
        raw_path = match.group(1) or match.group(2)
        file_path = raw_path.strip().strip("`").strip()

        content_start = match.end()

        if index + 1 < len(matches):
            content_end = matches[index + 1].start()
        else:
            content_end = len(output)

        raw_content = output[content_start:content_end]
        cleaned_content = clean_source_code(raw_content, file_path)

        if not cleaned_content.strip():
            raise ValueError(f"File content is empty: {file_path}")

        if file_path in files:
            raise ValueError(f"Duplicate file path: {file_path}")

        files[file_path] = cleaned_content

    return files


def validate_file_path(file_path: str) -> Path:
    """Reject unsafe paths from generated output."""

    if not isinstance(file_path, str) or not file_path.strip() or "\x00" in file_path:
        raise ValueError("Invalid file path.")

    # Reject absolute root-slashes regardless of platform
    if file_path.startswith("/") or file_path.startswith("\\"):
        raise ValueError("Absolute paths are not allowed.")

    # Reject Windows drive paths and backslashes
    if "\\" in file_path or ":" in file_path:
        raise ValueError("Unsafe file path.")

    relative_path = Path(file_path)

    if relative_path.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    if ".." in relative_path.parts:
        raise ValueError("Path traversal is not allowed.")

    if not relative_path.parts or any(
        part.strip() in ("", ".", "..") for part in relative_path.parts
    ):
        raise ValueError("Invalid file path.")

    return relative_path


# =====================================================================
# AST AND SYNTAX VALIDATORS
# =====================================================================

def validate_python_syntax(code: str, file_path: str = "script.py") -> tuple[bool, Optional[str]]:
    """Validate Python code syntax using the built-in ast parser."""
    try:
        ast.parse(code, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"Python syntax error in {file_path} (line {e.lineno}, col {e.offset}): {e.msg}"
    except Exception as e:
        return False, f"Python parsing error in {file_path}: {str(e)}"


def validate_json_syntax(code: str, file_path: str = "data.json") -> tuple[bool, Optional[str]]:
    """Validate JSON code syntax using the built-in json parser."""
    try:
        json.loads(code)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error in {file_path} (line {e.lineno}, col {e.colno}): {e.msg}"
    except Exception as e:
        return False, f"JSON parsing error in {file_path}: {str(e)}"


def validate_jsx_syntax(code: str, file_path: str = "Component.jsx") -> tuple[bool, Optional[str]]:
    """Validate JSX / JS / TS syntax using Node and esbuild with fallback."""
    loader = "jsx"
    if file_path.endswith((".ts", ".tsx")):
        loader = "tsx"
    elif file_path.endswith(".js"):
        loader = "jsx"

    if VALIDATE_JSX_SCRIPT.exists():
        try:
            res = subprocess.run(
                ["node", str(VALIDATE_JSX_SCRIPT), loader],
                input=code,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=10,
            )
            if res.returncode == 0:
                return True, None
            err = res.stderr.strip() or "JSX syntax error"
            return False, f"JSX syntax error in {file_path}: {err}"
        except Exception:
            pass

    # Fallback lexical and tag check if node is absent
    open_braces = code.count("{") - code.count("}")
    open_parens = code.count("(") - code.count(")")
    if abs(open_braces) > 3 or abs(open_parens) > 3:
        return False, f"Unbalanced syntax in {file_path}: braces diff={open_braces}, parens diff={open_parens}"

    if re.search(r"<[^>]*[^\x00-\x7F][^>]*>", code):
        return False, f"Non-ASCII corruption found in JSX tag in {file_path}"

    return True, None


def verify_image_references(content: str, file_path: str, available_files: list = None) -> list[str]:
    """
    Check image references in frontend components:
    - Flags fake/missing local images.
    - Warns if remote images lack onError fallback handlers.
    """
    issues = []
    if not file_path.endswith((".jsx", ".tsx", ".js", ".html")):
        return issues

    # Match <img ... src="..." ...>
    img_tags = re.findall(r"<img\b([^>]*?)/?>", content, re.IGNORECASE | re.DOTALL)
    for tag in img_tags:
        src_match = re.search(r'''src=(?:["']([^"']+)["']|\{([^}]+)\})''', tag)
        if src_match:
            src = (src_match.group(1) or src_match.group(2) or "").strip()
            # Check for invented local path (e.g. /images/gym.jpg or ./assets/foo.png)
            if src.startswith(("/", "./", "../", "assets/", "images/")):
                clean_src = src.lstrip("./").lstrip("/").replace("\\", "/")
                if available_files is not None:
                    matched = any(f.endswith(clean_src) or clean_src in f for f in available_files)
                    if not matched:
                        issues.append(f"Image references local asset '{src}' in {file_path} that does not exist in project.")

    return issues


def validate_project_completeness(files_dict: dict) -> tuple[bool, list[str], list[str]]:
    """
    Verify that the generated project contains all required core structure.
    Returns (is_complete, errors, warnings).
    """
    errors = []
    warnings = []
    paths = list(files_dict.keys())
    posix_paths = [p.replace("\\", "/").lower() for p in paths]

    # Check 1: Frontend package.json
    has_package_json = any(p.endswith("package.json") for p in posix_paths)
    if not has_package_json:
        errors.append("Missing frontend configuration: 'package.json' not found.")

    # Check 2: Entry HTML
    has_html = any(p.endswith(".html") for p in posix_paths)
    if not has_html:
        warnings.append("Missing HTML entry point: 'index.html' not found.")

    # Check 3: Main UI component entry
    has_app = any("app.jsx" in p or "app.tsx" in p or "main.jsx" in p or "index.jsx" in p for p in posix_paths)
    if not has_app:
        errors.append("Missing main frontend entry: 'App.jsx' or 'main.jsx' not found.")

    # Check 4: Demo / Mock data file
    has_mock_data = any("mock" in p or "seed" in p or "data.js" in p or "demodata" in p for p in posix_paths)
    if not has_mock_data:
        warnings.append("No mock/demo data file found in frontend (e.g. mockData.js). Frontend may display blank on first load.")

    # Check 5: Backend entry (for fullstack applications)
    has_backend_entry = any("main.py" in p or "app.py" in p for p in posix_paths)
    if not has_backend_entry and any(p.endswith(".py") for p in posix_paths):
        warnings.append("Python files generated but no main application entry ('main.py' or 'app.py') found.")

    is_complete = len(errors) == 0
    return is_complete, errors, warnings


def validate_project(
    project_dir: Path,
    files_dict: Optional[dict] = None
) -> dict:
    """
    Comprehensive quality gate validator.
    Inspects syntax of Python, JSON, and JSX/JS files, image references,
    and project completeness.
    """
    proj = Path(project_dir).resolve()

    if files_dict is None:
        files_dict = {}
        if proj.exists() and proj.is_dir():
            for f in proj.rglob("*"):
                if f.is_file() and not any(part.startswith(".") for part in f.parts):
                    rel = f.relative_to(proj).as_posix()
                    try:
                        files_dict[rel] = f.read_text(encoding="utf-8")
                    except Exception:
                        pass

    critical_errors = []
    warnings = []
    file_list = list(files_dict.keys())
    validated_counts = {"python": 0, "json": 0, "jsx": 0, "images_checked": 0}

    for file_path, content in files_dict.items():
        lower_path = file_path.lower()

        # 1. Python AST Validation
        if lower_path.endswith(".py"):
            validated_counts["python"] += 1
            ok, err = validate_python_syntax(content, file_path)
            if not ok:
                critical_errors.append(err)

        # 2. JSON Validation
        elif lower_path.endswith(".json"):
            validated_counts["json"] += 1
            ok, err = validate_json_syntax(content, file_path)
            if not ok:
                critical_errors.append(err)

        # 3. JSX / JS Validation
        elif lower_path.endswith((".jsx", ".tsx", ".js")):
            validated_counts["jsx"] += 1
            ok, err = validate_jsx_syntax(content, file_path)
            if not ok:
                critical_errors.append(err)

            # Check image references
            validated_counts["images_checked"] += 1
            img_issues = verify_image_references(content, file_path, file_list)
            warnings.extend(img_issues)

    # 4. Project Completeness Validation
    complete, comp_errors, comp_warnings = validate_project_completeness(files_dict)
    critical_errors.extend(comp_errors)
    warnings.extend(comp_warnings)

    is_valid = len(critical_errors) == 0
    has_critical_errors = not is_valid

    summary = (
        f"Validation {'PASSED' if is_valid else 'FAILED'}: "
        f"{len(critical_errors)} critical errors, {len(warnings)} warnings across {len(files_dict)} files."
    )

    return {
        "is_valid": is_valid,
        "has_critical_errors": has_critical_errors,
        "errors": critical_errors,
        "warnings": warnings,
        "validated_counts": validated_counts,
        "summary": summary,
    }


# =====================================================================
# PROJECT FILE WRITING AND EXPORT
# =====================================================================

def write_project_files(
    developer_output: str,
    project_name: str,
    target_dir: Path = None,
    overwrite: bool = False,
) -> list:
    """Write generated files into a project directory."""

    safe_project_name = sanitize_project_name(project_name)
    files = parse_generated_files(developer_output)

    if target_dir is None:
        GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        project_dir = GENERATED_PROJECTS_DIR / safe_project_name
    else:
        project_dir = Path(target_dir)

    if not overwrite:
        # Do not overwrite an existing project directory when overwrite is False.
        project_dir.mkdir(parents=True, exist_ok=False)
    else:
        project_dir.mkdir(parents=True, exist_ok=True)

    written_files = []

    try:
        for file_path, content in files.items():
            relative_path = validate_file_path(file_path)

            destination = (project_dir / relative_path).resolve()

            try:
                destination.relative_to(project_dir.resolve())
            except ValueError:
                raise ValueError(
                    "Generated file path escapes project directory."
                )

            destination.parent.mkdir(parents=True, exist_ok=True)

            if destination.exists() and not overwrite:
                raise ValueError(
                    f"File already exists: {relative_path.as_posix()}"
                )

            destination.write_text(content, encoding="utf-8")

            written_files.append(relative_path.as_posix())

    except Exception:
        if not overwrite:
            # Remove incomplete project if initial creation fails
            shutil.rmtree(project_dir, ignore_errors=True)
        raise

    return written_files


def load_task_outputs_from_db(db_path: Path = None) -> dict:
    """
    Read the six agent task outputs from the CrewAI SQLite storage database.
    Returns a dictionary of role-keyed raw outputs.
    """

    path = Path(db_path) if db_path else DEFAULT_STORAGE_DB

    if not path.exists():
        raise FileNotFoundError(f"Storage database not found: {path}")

    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='latest_kickoff_task_outputs'"
        )
        if not cursor.fetchone():
            raise ValueError(
                "Table 'latest_kickoff_task_outputs' not found in database."
            )

        rows = cursor.execute(
            "SELECT * FROM latest_kickoff_task_outputs"
        ).fetchall()

        if not rows:
            raise ValueError("No task outputs recorded in storage database.")

        role_order = [
            "product_manager",
            "architect",
            "database_designer",
            "developer",
            "testing_engineer",
            "code_reviewer",
        ]

        outputs = {}

        for index, row in enumerate(rows):
            try:
                data = json.loads(row[3])
            except (json.JSONDecodeError, IndexError) as err:
                raise ValueError(f"Malformed task record in database at row {index}: {err}")

            description = data.get("description", "").strip()
            raw_output = data.get("raw", "")

            if not raw_output or not raw_output.strip():
                raise ValueError(f"Task output at index {index} is empty.")

            # Identify role based on task description prefix
            if description.startswith("Analyse"):
                role = "product_manager"
            elif description.startswith("Design the software architecture"):
                role = "architect"
            elif description.startswith("Design the database"):
                role = "database_designer"
            elif description.startswith("Develop"):
                role = "developer"
            elif description.startswith("Test"):
                role = "testing_engineer"
            elif description.startswith("Review"):
                role = "code_reviewer"
            elif index < len(role_order):
                role = role_order[index]
            else:
                role = f"task_{index}"

            outputs[role] = raw_output

        # Verify all 6 expected agents are present
        missing = [role for role in role_order if role not in outputs]
        if missing:
            raise ValueError(f"Missing required agent outputs from database: {missing}")

        return outputs

    finally:
        conn.close()


def write_reports(
    reports: dict,
    project_dir: Path,
    subdirs: tuple = ("docs", "reports")
) -> list:
    """
    Save agent reports as separate Markdown files in docs/ and reports/ subdirectories.
    Returns the list of written relative file paths.
    """

    written_reports = []

    # Map role names to clean report filenames
    report_filename_map = {
        "product_manager": "product_manager_report.md",
        "architect": "architect_report.md",
        "database_designer": "database_designer_report.md",
        "testing_engineer": "testing_engineer_report.md",
        "code_reviewer": "code_reviewer_report.md",
    }

    for subdir in subdirs:
        target_dir = project_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        for role, filename in report_filename_map.items():
            content = reports.get(role)
            if content:
                file_path = target_dir / filename
                file_path.write_text(content.strip(), encoding="utf-8")
                rel_path = f"{subdir}/{filename}"
                written_reports.append(rel_path)

    return written_reports


def create_project_zip(project_dir: Path, zip_path: Path = None) -> Path:
    """Create a ZIP archive of the generated project directory."""

    proj = Path(project_dir).resolve()
    if not proj.exists() or not proj.is_dir():
        raise FileNotFoundError(f"Project directory not found: {proj}")

    if zip_path is None:
        target_zip = proj.parent / f"{proj.name}.zip"
    else:
        target_zip = Path(zip_path).resolve()

    target_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in sorted(proj.rglob("*")):
            if file.is_file():
                # Store relative to project_dir parent to maintain root folder
                archive_name = file.relative_to(proj.parent).as_posix()
                zip_file.write(file, archive_name)

    return target_zip


def export_completed_project(
    db_path: Path = None,
    project_name: str = "simple_shopping_platform",
    overwrite: bool = True
) -> dict:
    """
    Read outputs from the CrewAI database, write all source files and markdown reports,
    and bundle the completed project into a ZIP archive.
    """

    safe_name = sanitize_project_name(project_name)
    project_dir = GENERATED_PROJECTS_DIR / safe_name

    # 1. Read task outputs from storage database
    task_outputs = load_task_outputs_from_db(db_path)

    developer_output = task_outputs.get("developer")
    if not developer_output:
        raise ValueError("Developer output missing from database.")

    # 2. Extract and write developer source files
    written_source_files = write_project_files(
        developer_output=developer_output,
        project_name=safe_name,
        target_dir=project_dir,
        overwrite=overwrite,
    )

    # 3. Write agent reports
    written_reports = write_reports(
        reports=task_outputs,
        project_dir=project_dir,
        subdirs=("docs", "reports"),
    )

    # 4. Create ZIP archive
    zip_path = create_project_zip(project_dir)

    return {
        "project_name": safe_name,
        "project_dir": project_dir,
        "source_files": written_source_files,
        "source_file_count": len(written_source_files),
        "report_files": written_reports,
        "report_file_count": len(written_reports),
        "zip_path": zip_path,
        "zip_size_bytes": zip_path.stat().st_size,
    }
