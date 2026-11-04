
import tempfile
from pathlib import Path
from unittest.mock import patch

from services.project_writer import (
    parse_generated_files,
    sanitize_project_name,
    strip_code_fences,
    validate_file_path,
    write_project_files,
)


def test_project_name():
    """Test project name sanitization."""
    assert sanitize_project_name("My Shopping Platform") == "my_shopping_platform"
    assert sanitize_project_name("  Test App 123!@#  ") == "test_app_123"
    assert sanitize_project_name("E-COMMERCE_MVP") == "e-commerce_mvp"

    # Invalid names
    for invalid in ["", "   ", "---", "###", None, 123]:
        try:
            sanitize_project_name(invalid)
            raise AssertionError(f"Expected ValueError for invalid name: {invalid}")
        except ValueError:
            pass


def test_header_formats():
    """Test all three supported file header formats."""

    # Format 1: ### File: path
    sample_f1 = (
        "### File: backend/app/main.py\n"
        "```python\n"
        "def hello():\n"
        "    return 'world'\n"
        "```\n"
    )
    files_f1 = parse_generated_files(sample_f1)
    assert "backend/app/main.py" in files_f1
    assert files_f1["backend/app/main.py"] == "def hello():\n    return 'world'"

    # Format 2: ### File: `path`
    sample_f2 = (
        "### File: `frontend/src/App.jsx`\n"
        "```jsx\n"
        "export default function App() {\n"
        "    return <h1>Shopping</h1>;\n"
        "}\n"
        "```\n"
    )
    files_f2 = parse_generated_files(sample_f2)
    assert "frontend/src/App.jsx" in files_f2
    assert files_f2["frontend/src/App.jsx"] == (
        "export default function App() {\n"
        "    return <h1>Shopping</h1>;\n"
        "}"
    )

    # Format 3: ### `path`
    sample_f3 = (
        "### `database/init.sql`\n"
        "```sql\n"
        "CREATE TABLE users (\n"
        "    id UUID PRIMARY KEY,\n"
        "    email VARCHAR(255) NOT NULL\n"
        ");\n"
        "```\n"
    )
    files_f3 = parse_generated_files(sample_f3)
    assert "database/init.sql" in files_f3
    assert files_f3["database/init.sql"] == (
        "CREATE TABLE users (\n"
        "    id UUID PRIMARY KEY,\n"
        "    email VARCHAR(255) NOT NULL\n"
        ");"
    )


def test_fenced_languages_and_indentation():
    """Test fence stripping for Python, JavaScript/JSX, and SQL while preserving indentation."""

    python_snippet = (
        "class OrderService:\n"
        "    def __init__(self, db_session):\n"
        "        self.db = db_session\n"
        "\n"
        "    def calculate_total(self, items):\n"
        "        subtotal = sum(i.price for i in items)\n"
        "        if subtotal >= 5000:\n"
        "            shipping = 0\n"
        "        else:\n"
        "            shipping = 500\n"
        "        return subtotal + shipping"
    )

    js_snippet = (
        "import React, { useState } from 'react';\n"
        "\n"
        "export function Cart() {\n"
        "    const [items, setItems] = useState([]);\n"
        "    return (\n"
        "        <div className=\"cart\">\n"
        "            <h2>Your Cart</h2>\n"
        "        </div>\n"
        "    );\n"
        "}"
    )

    sql_snippet = (
        "CREATE TABLE products (\n"
        "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    name VARCHAR(150) NOT NULL,\n"
        "    price_cents INTEGER NOT NULL CHECK (price_cents > 0)\n"
        ");"
    )

    sample = (
        f"### `backend/services/orders.py`\n"
        f"```python\n{python_snippet}\n```\n\n"
        f"### File: `frontend/components/Cart.jsx`\n"
        f"```javascript\n{js_snippet}\n```\n\n"
        f"### File: database/schema.sql\n"
        f"```sql\n{sql_snippet}\n```\n"
    )

    files = parse_generated_files(sample)

    assert len(files) == 3
    assert files["backend/services/orders.py"] == python_snippet
    assert files["frontend/components/Cart.jsx"] == js_snippet
    assert files["database/schema.sql"] == sql_snippet

    # Verify no backticks or language tags leaked
    for path, content in files.items():
        assert not content.startswith("```"), f"Opening fence leaked into {path}"
        assert not content.endswith("```"), f"Closing fence leaked into {path}"
        assert not content.startswith("python"), f"Language label leaked into {path}"
        assert not content.startswith("javascript"), f"Language label leaked into {path}"
        assert not content.startswith("sql"), f"Language label leaked into {path}"


def test_unfenced_code_and_internal_fences():
    """Test unfenced code passthrough and code containing internal markdown fences."""

    # Unfenced code
    unfenced = "### File: config.txt\nKEY=VALUE\nPORT=8000\n"
    files = parse_generated_files(unfenced)
    assert files["config.txt"] == "KEY=VALUE\nPORT=8000"

    # Markdown file containing internal code blocks
    markdown_doc = (
        "# Documentation\n"
        "\n"
        "Run this command:\n"
        "```bash\n"
        "npm run dev\n"
        "```\n"
        "\n"
        "Finished."
    )
    sample_doc = f"### `README.md`\n```markdown\n{markdown_doc}\n```\n"
    files_doc = parse_generated_files(sample_doc)
    assert files_doc["README.md"] == markdown_doc


def test_multiple_files_in_one_output():
    """Test parsing multiple files across various directories."""

    sample = (
        "### `.env.example`\n"
        "```env\n"
        "DATABASE_URL=sqlite:///./test.db\n"
        "```\n\n"
        "### `backend/main.py`\n"
        "```python\n"
        "print('backend')\n"
        "```\n\n"
        "### File: frontend/index.html\n"
        "```html\n"
        "<!DOCTYPE html><html><body>App</body></html>\n"
        "```\n\n"
        "### File: `database/init.sql`\n"
        "```sql\n"
        "SELECT 1;\n"
        "```\n"
    )

    files = parse_generated_files(sample)
    assert len(files) == 4
    assert ".env.example" in files
    assert "backend/main.py" in files
    assert "frontend/index.html" in files
    assert "database/init.sql" in files


def test_empty_or_malformed_output():
    """Test rejection of empty, whitespace, non-string, or header-less outputs."""

    # Empty and invalid outputs
    for invalid in ["", "   \n\t  ", None, 12345]:
        try:
            parse_generated_files(invalid)
            raise AssertionError(f"Expected ValueError for: {invalid}")
        except ValueError:
            pass

    # No headers found
    try:
        parse_generated_files("Here is the code without any file headers:\ndef foo(): pass")
        raise AssertionError("Expected ValueError when no headers are present")
    except ValueError:
        pass

    # Empty content under header
    try:
        parse_generated_files("### File: empty.py\n\n### File: next.py\nprint(1)")
        raise AssertionError("Expected ValueError for empty file content")
    except ValueError:
        pass

    # Duplicate file header
    try:
        parse_generated_files(
            "### File: duplicate.py\nprint(1)\n\n### File: duplicate.py\nprint(2)\n"
        )
        raise AssertionError("Expected ValueError for duplicate file header")
    except ValueError:
        pass


def test_reject_unsafe_paths():
    """Test strict rejection of directory traversal and unsafe file paths."""

    unsafe_paths = [
        "../../secret.txt",
        "../outside.py",
        "backend/../../secret.txt",
        "/etc/passwd",
        "/var/log/app.log",
        "\\Windows\\System32\\calc.exe",
        "C:\\Windows\\win.ini",
        "C:/autoexec.bat",
        "D:data.txt",
        "backend\\main.py",
        "path/with/\x00/nullbyte",
        "",
        "   ",
        ".",
        "..",
        None,
    ]

    for path in unsafe_paths:
        try:
            validate_file_path(path)
            raise AssertionError(f"Expected ValueError for unsafe path: {path}")
        except ValueError:
            pass


def test_write_project_files_to_disk():
    """Test writing actual files into a project directory on disk."""

    sample = (
        "### `backend/app/main.py`\n"
        "```python\n"
        "def main():\n"
        "    return {'status': 'ok'}\n"
        "```\n\n"
        "### File: `frontend/App.jsx`\n"
        "```jsx\n"
        "export default function App() {\n"
        "    return <div>Hello</div>;\n"
        "}\n"
        "```\n\n"
        "### File: database/init.sql\n"
        "```sql\n"
        "CREATE TABLE test (id INT);\n"
        "```\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        test_root = Path(temp_dir)

        with patch("services.project_writer.GENERATED_PROJECTS_DIR", test_root):
            written = write_project_files(sample, "My Test App")

            assert len(written) == 3
            assert "backend/app/main.py" in written
            assert "frontend/App.jsx" in written
            assert "database/init.sql" in written

            # Verify backend file on disk
            backend_file = test_root / "my_test_app" / "backend" / "app" / "main.py"
            assert backend_file.exists()
            content = backend_file.read_text(encoding="utf-8")
            assert content == "def main():\n    return {'status': 'ok'}"
            assert "```" not in content

            # Verify frontend file on disk
            frontend_file = test_root / "my_test_app" / "frontend" / "App.jsx"
            assert frontend_file.exists()
            content = frontend_file.read_text(encoding="utf-8")
            assert "export default function App()" in content
            assert "```" not in content

            # Verify database file on disk
            db_file = test_root / "my_test_app" / "database" / "init.sql"
            assert db_file.exists()
            content = db_file.read_text(encoding="utf-8")
            assert content == "CREATE TABLE test (id INT);"
            assert "```" not in content

            # Verify project overwrite protection
            try:
                write_project_files(sample, "My Test App")
                raise AssertionError("Expected FileExistsError when project directory already exists")
            except FileExistsError:
                pass


if __name__ == "__main__":
    test_project_name()
    test_header_formats()
    test_fenced_languages_and_indentation()
    test_unfenced_code_and_internal_fences()
    test_multiple_files_in_one_output()
    test_empty_or_malformed_output()
    test_reject_unsafe_paths()
    test_write_project_files_to_disk()

    print("All project writer unit tests passed successfully!")
