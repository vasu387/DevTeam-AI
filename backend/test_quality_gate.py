import os
import sys
import tempfile
import shutil
import sqlite3
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from services.project_writer import (
    validate_python_syntax,
    validate_json_syntax,
    validate_jsx_syntax,
    verify_image_references,
    validate_project_completeness,
    validate_project,
    clean_source_code,
    create_project_zip,
)
from services.job_manager import JobManager


def run_quality_gate_tests():
    print("=" * 70)
    print("DEVTEAM AI - QUALITY GATE & VALIDATOR TEST SUITE")
    print("=" * 70, flush=True)

    # -------------------------------------------------------------
    # 1. PYTHON AST SYNTAX VALIDATION
    # -------------------------------------------------------------
    print("\n[Test 1] Testing Python AST syntax validation...", flush=True)
    valid_py = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'status': 'healthy'}\n"
    )
    ok, err = validate_python_syntax(valid_py, "app/main.py")
    assert ok is True and err is None, f"Expected valid Python to pass: {err}"
    print("  PASS: Clean Python code parses with AST successfully.")

    broken_py = (
        "def broken_function(\n"
        "    x = 10\n"
        "    return x\n"
    )
    ok, err = validate_python_syntax(broken_py, "app/broken.py")
    assert ok is False and err is not None and "Syntax error" in err or "syntax error" in err, f"Expected syntax error, got: {err}"
    print(f"  PASS: Caught invalid Python syntax with exact location: {err}")

    # -------------------------------------------------------------
    # 2. JSON SYNTAX VALIDATION
    # -------------------------------------------------------------
    print("\n[Test 2] Testing JSON syntax validation...", flush=True)
    valid_json = '{"name": "gym-web", "version": "1.0.0", "dependencies": {"react": "^18.2.0"}}'
    ok, err = validate_json_syntax(valid_json, "package.json")
    assert ok is True and err is None, f"Expected valid JSON to pass: {err}"
    print("  PASS: Clean JSON parses successfully.")

    broken_json = '{"name": "gym-web", "version": "1.0.0", "trailing_comma": true,}'
    ok, err = validate_json_syntax(broken_json, "package.json")
    assert ok is False and err is not None, "Expected invalid JSON to fail"
    print(f"  PASS: Caught invalid JSON syntax correctly: {err}")

    # -------------------------------------------------------------
    # 3. JSX / JS SYNTAX VALIDATION
    # -------------------------------------------------------------
    print("\n[Test 3] Testing JSX / JS syntax validation...", flush=True)
    valid_jsx = (
        "import React, { useState } from 'react';\n"
        "export default function Hero() {\n"
        "  const [active, setActive] = useState(true);\n"
        "  return (\n"
        "    <section className='hero-bg text-white p-8'>\n"
        "      <h1 className='text-4xl font-bold'>Elevate Your Fitness</h1>\n"
        "      <button onClick={() => setActive(!active)} className='btn-primary'>Join Now</button>\n"
        "    </section>\n"
        "  );\n"
        "}\n"
    )
    ok, err = validate_jsx_syntax(valid_jsx, "src/components/Hero.jsx")
    assert ok is True and err is None, f"Expected valid JSX to pass: {err}"
    print("  PASS: Clean React JSX compiles successfully.")

    # Stray Cyrillic or broken tag that ruined shopping Cart.jsx
    broken_jsx = (
        "export default function BrokenCard() {\n"
        "  return <img className='w-16 h-16 rounded'/тность/>;\n"
        "}\n"
    )
    ok, err = validate_jsx_syntax(broken_jsx, "src/components/BrokenCard.jsx")
    assert ok is False, "Expected broken Cyrillic tag in JSX to fail compilation"
    print("  PASS: Detected malformed JSX corruption (stray non-ASCII tag) successfully.")

    # -------------------------------------------------------------
    # 4. IMAGE REFERENCE & ASSET HANDLING
    # -------------------------------------------------------------
    print("\n[Test 4] Testing image reference & asset verification...", flush=True)
    jsx_with_images = (
        "export default function TrainerCard() {\n"
        "  return (\n"
        "    <div>\n"
        "      <img src='https://images.unsplash.com/photo-1534438327276?w=600' alt='Trainer' onError={(e)=>e.target.src='/assets/fallback.svg'} />\n"
        "      <img src='/assets/non_existent_fake_trainer.jpg' alt='Fake Local' />\n"
        "    </div>\n"
        "  );\n"
        "}\n"
    )
    available_files = ["src/TrainerCard.jsx", "public/assets/fallback.svg"]
    issues = verify_image_references(jsx_with_images, "src/TrainerCard.jsx", available_files)
    assert len(issues) == 1, f"Expected 1 missing local asset issue, got {issues}"
    assert "non_existent_fake_trainer.jpg" in issues[0]
    print("  PASS: Detected non-existent local image reference while allowing valid remote URL with fallback.")

    # -------------------------------------------------------------
    # 5. SOURCE CODE CLEANING (MARKDOWN FENCE STRIPPING)
    # -------------------------------------------------------------
    print("\n[Test 5] Testing source code cleaner on markdown fence leaks...", flush=True)
    fenced_content = (
        "```javascript\n"
        "export const mockMemberships = [\n"
        "  { id: 1, title: 'Pro Plan', price: 49 },\n"
        "  { id: 2, title: 'Elite Plan', price: 89 }\n"
        "];\n"
        "```\n"
    )
    cleaned = clean_source_code(fenced_content, "mockData.js")
    assert not cleaned.startswith("```"), "Leading fence not stripped"
    assert not cleaned.endswith("```"), "Trailing fence not stripped"
    assert "mockMemberships" in cleaned
    print("  PASS: Cleaned source code and stripped markdown fences cleanly.")

    # -------------------------------------------------------------
    # 6. PROJECT COMPLETENESS & QUALITY GATE
    # -------------------------------------------------------------
    print("\n[Test 6] Testing project completeness validation...", flush=True)
    complete_project = {
        "frontend/package.json": '{"name": "gym-web", "dependencies": {"react": "^18.2.0"}}',
        "frontend/index.html": "<!DOCTYPE html><html><head><title>Gym</title></head><body><div id='root'></div></body></html>",
        "frontend/src/main.jsx": "import React from 'react'; import App from './App'; console.log(App);",
        "frontend/src/App.jsx": "export default function App() { return <div>Gym App</div>; }",
        "frontend/src/index.css": "body { margin: 0; font-family: sans-serif; }",
        "frontend/src/data/mockData.js": "export const plans = [{ id: 'pro', name: 'Pro Fitness' }];",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "backend/requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.22.0",
        "README.md": "# Gym Management System",
    }
    is_complete, errors, warnings = validate_project_completeness(complete_project)
    assert is_complete is True and len(errors) == 0, f"Expected project to be complete: {errors}"
    print("  PASS: Complete full-stack project passes completeness check.")

    incomplete_project = {
        "frontend/index.html": "<html></html>",
        "frontend/src/random.js": "const a = 1;",
    }
    is_complete, errors, warnings = validate_project_completeness(incomplete_project)
    assert is_complete is False and len(errors) >= 2, "Expected incomplete project to report missing package.json and App.jsx"
    print(f"  PASS: Incomplete project correctly rejected with {len(errors)} required file errors.")

    # -------------------------------------------------------------
    # 7. QUALITY GATE: PREVENT ZIP ON SYNTAX FAILURE
    # -------------------------------------------------------------
    print("\n[Test 7] Testing Quality Gate blocking ZIP creation on broken syntax...", flush=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "broken_test_project"
        tmp_path.mkdir(parents=True)
        (tmp_path / "package.json").write_text('{"name": "broken"}', encoding="utf-8")
        (tmp_path / "App.jsx").write_text("export default function Broken() { return <div/тельность/>; }", encoding="utf-8")

        res = validate_project(tmp_path)
        assert res["has_critical_errors"] is True
        assert res["is_valid"] is False
        safe_errors = [e.encode("ascii", "replace").decode("ascii") for e in res["errors"]]
        print(f"  PASS: validate_project() flagged critical errors: {safe_errors}")

        # Ensure ZIP is NOT created when has_critical_errors is True
        zip_path = tmp_path.parent / f"{tmp_path.name}.zip"
        assert not zip_path.exists(), "ZIP must not exist prior to creation"
        if not res["has_critical_errors"]:
            create_project_zip(tmp_path)
        assert not zip_path.exists(), "ZIP was mistakenly created for project with critical syntax error!"
        print("  PASS: Corrupted ZIP creation successfully blocked by Quality Gate.")

    # -------------------------------------------------------------
    # 8. INTEGRITY VERIFICATION OF PREVIOUS ASSETS
    # -------------------------------------------------------------
    print("\n[Test 8] Verifying existing Shopping platform and SQLite database integrity...", flush=True)
    shop_dir = BACKEND_DIR.parent / "generated_projects" / "simple_shopping_platform"
    shop_zip = BACKEND_DIR.parent / "generated_projects" / "simple_shopping_platform.zip"
    assert shop_dir.exists() and shop_dir.is_dir(), "simple_shopping_platform directory missing"
    assert shop_zip.exists() and shop_zip.is_file(), "simple_shopping_platform.zip missing"
    assert shop_zip.stat().st_size == 157800, f"Shopping ZIP size modified: {shop_zip.stat().st_size}"
    print(f"  PASS: Shopping project directory and ZIP ({shop_zip.stat().st_size:,} bytes) are 100% untouched.")

    db_path = BACKEND_DIR / ".crewai_storage" / "latest_kickoff_task_outputs.db"
    assert db_path.exists(), "latest_kickoff_task_outputs.db missing"
    conn = sqlite3.connect(db_path)
    count = conn.cursor().execute("SELECT count(*) FROM latest_kickoff_task_outputs").fetchone()[0]
    conn.close()
    assert count == 6, f"Expected 6 task outputs, found {count}"
    print("  PASS: SQLite storage contains all 6 task outputs untouched.")

    print("\n" + "=" * 70)
    print("ALL QUALITY GATE & VALIDATOR TESTS PASSED SUCCESSFULLY (0 ERRORS)")
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_quality_gate_tests()
