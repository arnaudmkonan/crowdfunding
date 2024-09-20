import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

def test_dashboard_authentication():
    # Test unauthenticated access
    response = client.get("/dashboard")
    assert response.status_code == 401  # Unauthorized
    assert "login.html" in response.text
    assert "Please log in to access the dashboard" in response.text

    # Test authenticated access
    access_token = create_access_token(data={"sub": "testuser"})
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/dashboard", headers=headers)
    assert response.status_code == 200
    assert "Dashboard" in response.text
