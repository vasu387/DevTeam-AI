import sys
import zipfile
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.project_writer import (
    GENERATED_PROJECTS_DIR,
    export_completed_project,
    load_task_outputs_from_db,
)


def test_export_verification():
    print("=" * 60)
    print("Testing Project Export from CrewAI Storage Database")
    print("=" * 60)

    # 1. Test database loader directly
    print("\n[Step 1] Loading task outputs from storage database...")
    task_outputs = load_task_outputs_from_db()

    expected_roles = [
        "product_manager",
        "architect",
        "database_designer",
        "developer",
        "testing_engineer",
        "code_reviewer",
    ]

    for role in expected_roles:
        assert role in task_outputs, f"Missing role in database: {role}"
        assert len(task_outputs[role]) > 500, f"Output too short for {role}"
        print(f"  PASS: Role '{role}' loaded ({len(task_outputs[role]):,} chars)")

    # 2. Execute export into generated_projects/simple_shopping_platform
    print("\n[Step 2] Executing export...")
    result = export_completed_project(
        project_name="simple_shopping_platform",
        overwrite=True,
    )

    project_dir = Path(result["project_dir"])
    source_files = result["source_files"]
    report_files = result["report_files"]
    zip_path = Path(result["zip_path"])

    assert project_dir.exists() and project_dir.is_dir(), f"Project dir missing: {project_dir}"
    assert len(source_files) >= 38, f"Expected at least 38 source files, found {len(source_files)}"
    assert len(report_files) >= 5, f"Expected at least 5 report files, found {len(report_files)}"
    print(f"  PASS: Exported {len(source_files)} source files and {len(report_files)} report files.")

    # 3. Verify key source files on disk
    print("\n[Step 3] Verifying source files on disk...")
    critical_files = [
        ".env.example",
        "docker-compose.yml",
        "README.md",
        "database/init.sql",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/database.py",
        "backend/app/models.py",
        "backend/app/schemas.py",
        "backend/app/security.py",
        "backend/app/pricing.py",
        "backend/app/seed.py",
        "backend/app/routers/auth.py",
        "backend/app/routers/catalog.py",
        "backend/app/routers/cart.py",
        "backend/app/routers/checkout_orders.py",
        "backend/app/routers/admin.py",
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/index.html",
        "frontend/src/main.jsx",
        "frontend/src/App.jsx",
        "frontend/src/index.css",
        "frontend/src/lib/api.js",
        "frontend/src/lib/pricing.js",
        "frontend/src/store/Store.jsx",
        "frontend/src/components/Layout.jsx",
        "frontend/src/pages/Home.jsx",
        "frontend/src/pages/Products.jsx",
        "frontend/src/pages/ProductDetail.jsx",
        "frontend/src/pages/Cart.jsx",
        "frontend/src/pages/Checkout.jsx",
        "frontend/src/pages/Orders.jsx",
        "frontend/src/pages/Auth.jsx",
        "frontend/src/pages/Admin.jsx",
        "frontend/src/pages/Static.jsx",
    ]

    for rel_path in critical_files:
        full_path = project_dir / rel_path
        assert full_path.exists(), f"Critical file missing on disk: {rel_path}"
        assert full_path.stat().st_size > 0, f"File is empty: {rel_path}"

        # Ensure no markdown code fence wrappers leaked into code
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        if not rel_path.endswith(".md"):
            assert not content.strip().startswith("```"), f"Opening fence leaked into {rel_path}"
            assert not content.strip().endswith("```"), f"Closing fence leaked into {rel_path}"

    print(f"  PASS: All {len(critical_files)} critical source files verified on disk.")

    # 4. Verify markdown reports
    print("\n[Step 4] Verifying agent reports...")
    expected_reports = [
        "product_manager_report.md",
        "architect_report.md",
        "database_designer_report.md",
        "testing_engineer_report.md",
        "code_reviewer_report.md",
    ]

    for rep in expected_reports:
        # Check docs/
        doc_path = project_dir / "docs" / rep
        assert doc_path.exists(), f"Report missing in docs/: {rep}"
        assert doc_path.stat().st_size > 1000, f"Report too small: {rep}"

        # Check reports/
        rep_path = project_dir / "reports" / rep
        assert rep_path.exists(), f"Report missing in reports/: {rep}"
        assert rep_path.stat().st_size > 1000, f"Report too small: {rep}"

    print(f"  PASS: All {len(expected_reports)} reports verified in docs/ and reports/.")

    # 5. Verify ZIP archive
    print("\n[Step 5] Verifying ZIP archive integrity...")
    assert zip_path.exists(), f"ZIP archive missing: {zip_path}"
    assert zip_path.stat().st_size > 5000, f"ZIP archive suspiciously small: {zip_path.stat().st_size} bytes"

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Test ZIP integrity (returns None if no corruption)
        bad_file = zf.testzip()
        assert bad_file is None, f"ZIP file corrupted at: {bad_file}"

        namelist = zf.namelist()
        assert len(namelist) >= len(critical_files), f"ZIP namelist count ({len(namelist)}) less than critical files"

        # Check sample paths inside zip
        assert "simple_shopping_platform/backend/app/main.py" in namelist
        assert "simple_shopping_platform/frontend/package.json" in namelist
        assert "simple_shopping_platform/docs/product_manager_report.md" in namelist

    print(f"  PASS: ZIP archive is valid with {len(namelist)} items ({zip_path.stat().st_size:,} bytes).")

    print("\n" + "=" * 60)
    print("ALL PROJECT EXPORT VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_export_verification()

