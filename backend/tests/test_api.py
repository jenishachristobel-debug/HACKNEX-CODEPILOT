import io
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'database' in data


def test_projects_upload_and_listing():
    repo_files = {
        'app.py': 'def add(a, b):\n    return a + b\n',
        'tests/test_app.py': 'from app import add\n\ndef test_add():\n    assert add(2, 3) == 5\n',
    }

    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, 'w') as zf:
        for relative_path, content in repo_files.items():
            zf.writestr(relative_path, content)

    memory_zip.seek(0)
    response = client.post(
        '/api/projects/upload',
        files={'file': ('demo.zip', memory_zip.getvalue(), 'application/zip')},
        data={'project_name': 'Demo Repo'},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data['project']['name'] == 'Demo Repo'
    assert data['project']['language'] == 'python'

    list_response = client.get('/api/projects')
    assert list_response.status_code == 200
    projects = list_response.json()['projects']
    assert len(projects) >= 1


def test_rejects_path_traversal_in_upload():
    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, 'w') as zf:
        zf.writestr('../../evil.py', 'print("evil")')
    memory_zip.seek(0)

    response = client.post(
        '/api/projects/upload',
        files={'file': ('evil.zip', memory_zip.getvalue(), 'application/zip')},
        data={'project_name': 'Bad Repo'},
    )

    assert response.status_code == 400
    assert 'path traversal' in response.json()['detail'].lower()


def test_patch_validation_rejects_invalid_patch():
    response = client.post(
        '/api/patches/validate',
        json={
            'project_id': 999,
            'patch': {
                'target_file': '../../etc/passwd',
                'new_code': 'print(1)'
            }
        }
    )
    assert response.status_code == 400
    assert 'invalid' in response.json()['detail'].lower()
