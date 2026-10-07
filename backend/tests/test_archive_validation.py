import io
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.config import settings

client = TestClient(app)


def _create_zip_bytes(files_dict: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for filename, content in files_dict.items():
            zf.writestr(filename, content)
    return buf.getvalue()


# 1. Valid ZIP containing Python files
def test_valid_python_zip_upload():
    zip_bytes = _create_zip_bytes({
        "main.py": "def hello(): return 'world'\n",
        "tests/test_main.py": "from main import hello\ndef test_hello(): assert hello() == 'world'\n"
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("python_project.zip", zip_bytes, "application/zip")},
        data={"project_name": "Python Project"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["project"]["name"] == "Python Project"
    assert data["project"]["language"] == "python"
    assert data["scan"]["python_files"] >= 2


# 2. Valid ZIP with top-level root directory (e.g. genslide-ai/app.py)
def test_valid_zip_with_top_level_root_directory():
    zip_bytes = _create_zip_bytes({
        "genslide-ai/app.py": "def run(): pass\n",
        "genslide-ai/requirements.txt": "pytest==8.0.0\n",
        "genslide-ai/tests/test_app.py": "def test_run(): pass\n"
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("genslide-ai.zip", zip_bytes, "application/zip")},
        data={"project_name": "Genslide Root Dir"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["project"]["name"] == "Genslide Root Dir"
    assert data["scan"]["python_files"] == 2


# 3. Valid ZIP containing nested folders
def test_valid_zip_containing_nested_folders():
    zip_bytes = _create_zip_bytes({
        "src/core/services/deep/processor.py": "def process(): return 42\n",
        "tests/unit/core/test_processor.py": "def test_p(): pass\n"
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("nested.zip", zip_bytes, "application/zip")},
        data={"project_name": "Nested Project"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["scan"]["python_files"] == 2


# 4. Valid ZIP containing spaces in filenames
def test_valid_zip_containing_spaces_in_filenames():
    zip_bytes = _create_zip_bytes({
        "My Core Service/main app.py": "print('hello with space')\n",
        "My Core Service/tests/test main.py": "def test_it(): pass\n"
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("spaces.zip", zip_bytes, "application/zip")},
        data={"project_name": "Spaces Project"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["scan"]["python_files"] == 2


# 5. Corrupted ZIP file (invalid bytes)
def test_corrupted_zip_file_rejected():
    corrupt_bytes = b"PK\x03\x04corrupted_header_data_not_a_valid_zip_payload"
    res = client.post(
        "/api/projects/upload",
        files={"file": ("corrupt.zip", corrupt_bytes, "application/zip")},
        data={"project_name": "Corrupt Repo"}
    )
    assert res.status_code == 400
    assert "not a valid zip archive" in res.json()["detail"].lower()


# 6. Non-ZIP file renamed to .zip
def test_renamed_non_zip_file_rejected():
    text_bytes = b"Hello, this is just a plain text file renamed to .zip!"
    res = client.post(
        "/api/projects/upload",
        files={"file": ("fake.zip", text_bytes, "application/zip")},
        data={"project_name": "Fake ZIP"}
    )
    assert res.status_code == 400
    assert "not a valid zip archive" in res.json()["detail"].lower()


# 7. Empty ZIP archive (0 files)
def test_empty_zip_archive_rejected():
    empty_zip = io.BytesIO()
    with zipfile.ZipFile(empty_zip, "w") as _:
        pass
    res = client.post(
        "/api/projects/upload",
        files={"file": ("empty.zip", empty_zip.getvalue(), "application/zip")},
        data={"project_name": "Empty Repo"}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# 8. Archive exceeding 25 MB
def test_archive_exceeding_max_size_rejected():
    with patch("app.config.settings.MAX_ARCHIVE_SIZE_BYTES", 1024):
        large_bytes = b"0" * 2048
        res = client.post(
            "/api/projects/upload",
            files={"file": ("large.zip", large_bytes, "application/zip")},
            data={"project_name": "Large Repo"}
        )
        assert res.status_code == 400
        assert "exceeds maximum allowed limit" in res.json()["detail"].lower()


# 9. Unix-style path traversal (../../evil.py)
def test_unix_path_traversal_rejected():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.py", "print('evil')")
    res = client.post(
        "/api/projects/upload",
        files={"file": ("traversal.zip", buf.getvalue(), "application/zip")},
        data={"project_name": "Traversal Repo"}
    )
    assert res.status_code == 400
    assert "path traversal detected" in res.json()["detail"].lower()


# 10. Windows-style path traversal (..\..\evil.py, C:\evil.py, /evil.py, \evil.py)
def test_windows_path_traversal_rejected():
    traversal_cases = [
        "..\\..\\evil.py",
        "C:\\evil.py",
        "/evil.py",
        "\\evil.py",
    ]
    for bad_path in traversal_cases:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(bad_path, "print('evil')")
        res = client.post(
            "/api/projects/upload",
            files={"file": ("bad_windows.zip", buf.getvalue(), "application/zip")},
            data={"project_name": "Bad Windows"}
        )
        assert res.status_code == 400, f"Failed to reject traversal pattern: {bad_path}"
        assert "path traversal detected" in res.json()["detail"].lower()


# 11. Symlink entries rejection
def test_symlink_entries_rejected():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("safe.py", "print('ok')\n")
        zf.writestr("link", "content")
        zf.getinfo("link").external_attr = 0o120777 << 16
    res = client.post(
        "/api/projects/upload",
        files={"file": ("symlink.zip", buf.getvalue(), "application/zip")},
        data={"project_name": "Symlink Repo"}
    )
    assert res.status_code == 400
    assert "symlink" in res.json()["detail"].lower()


# 12. Archive with .git and .env (safely ignored, not extracted)
def test_git_and_env_safely_ignored():
    zip_bytes = _create_zip_bytes({
        ".git/config": "[core]\nrepositoryformatversion = 0\n",
        ".env": "SECRET_KEY=supersecret\n",
        ".env.production": "DATABASE_URL=postgres://admin\n",
        "app.py": "def add(x, y): return x + y\n"
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("secrets.zip", zip_bytes, "application/zip")},
        data={"project_name": "Ignored Secrets"}
    )
    assert res.status_code == 200, res.text
    project_id = res.json()["project"]["id"]

    # Verify that in storage, .env and .git were never extracted
    project_dir = settings.PROJECTS_DIR / f"project_{project_id}"
    assert not (project_dir / ".env").exists()
    assert not (project_dir / ".env.production").exists()
    assert not (project_dir / ".git").exists()
    assert (project_dir / "app.py").exists()


# 13. Valid ZIP containing only JavaScript/TypeScript files (clear diagnostic message)
def test_javascript_typescript_zip_produces_language_diagnostic():
    zip_bytes = _create_zip_bytes({
        "package.json": '{"name": "genslide-ai", "version": "1.0.0"}',
        "tsconfig.json": '{"compilerOptions": {}}',
        "src/App.tsx": 'export const App = () => <div>Hello</div>;',
        "server.ts": 'console.log("Server running");'
    })
    res = client.post(
        "/api/projects/upload",
        files={"file": ("genslide-ai---ai-presentation-maker.zip", zip_bytes, "application/zip")},
        data={"project_name": "GENSLIDE"}
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "ZIP uploaded successfully, but no Python files were found." in detail
    assert "JavaScript/TypeScript" in detail


# 14. Upload field-name consistency (file and project_name)
def test_upload_field_name_validation():
    zip_bytes = _create_zip_bytes({"main.py": "print(1)\n"})
    # Missing project_name
    res = client.post(
        "/api/projects/upload",
        files={"file": ("test.zip", zip_bytes, "application/zip")}
    )
    assert res.status_code == 422

    # Wrong file field name
    res = client.post(
        "/api/projects/upload",
        files={"archive": ("test.zip", zip_bytes, "application/zip")},
        data={"project_name": "Testing"}
    )
    assert res.status_code == 422


# 15. Clean cleanup of staging directory on failed extraction or validation
def test_staging_directory_cleanup_on_failure():
    staging_dir = settings.STORAGE_DIR / "staging"
    before_dirs = set(os.listdir(staging_dir)) if staging_dir.exists() else set()

    # Upload corrupt zip
    client.post(
        "/api/projects/upload",
        files={"file": ("corrupt.zip", b"invalid_zip", "application/zip")},
        data={"project_name": "Clean Check"}
    )
    after_dirs = set(os.listdir(staging_dir)) if staging_dir.exists() else set()
    assert after_dirs == before_dirs, f"Staging directory leaked files: {after_dirs - before_dirs}"

    # Upload JS zip (which fails language check)
    js_zip = _create_zip_bytes({"index.js": "console.log(1);"})
    client.post(
        "/api/projects/upload",
        files={"file": ("js.zip", js_zip, "application/zip")},
        data={"project_name": "JS Check"}
    )
    after_js_dirs = set(os.listdir(staging_dir)) if staging_dir.exists() else set()
    assert after_js_dirs == before_dirs, f"Staging directory leaked after JS rejection: {after_js_dirs - before_dirs}"


# 16. Upload with 'name' form field alias
def test_upload_with_name_field_alias():
    zip_bytes = _create_zip_bytes({"main.py": "def test(): return True\n"})
    res = client.post(
        "/api/projects/upload",
        files={"file": ("name_alias.zip", zip_bytes, "application/zip")},
        data={"name": "Name Alias Project"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["project"]["name"] == "Name Alias Project"


# 17. Upload with both 'name' and 'project_name' provided
def test_upload_with_both_name_and_project_name():
    zip_bytes = _create_zip_bytes({"main.py": "def test(): return True\n"})
    res = client.post(
        "/api/projects/upload",
        files={"file": ("dual_fields.zip", zip_bytes, "application/zip")},
        data={"name": "Dual Field Name", "project_name": "Dual Field Project Name"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["project"]["name"] in ["Dual Field Name", "Dual Field Project Name"]

