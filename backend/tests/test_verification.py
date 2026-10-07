import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)


def test_verification_status_shapes():
    response = client.get('/api/health')
    assert response.status_code == 200
    payload = response.json()
    assert 'version' in payload
    assert 'execution_mode' in payload
