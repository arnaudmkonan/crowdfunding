import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Project

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)

@pytest.fixture(scope="function")
def test_user(client):
    user_data = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="function")
def test_project(client, test_user):
    project_data = {
        "title": "Test Project",
        "description": "A test project",
        "goal_amount": 10000,
        "creator_id": test_user["id"]
    }
    response = client.post("/api/projects/", json=project_data)
    assert response.status_code == 201
    return response.json()
from app.auth import create_access_token

def test_dashboard_authentication(client, test_user):
    # Test unauthenticated access
    response = client.get("/dashboard")
    assert response.status_code == 401  # Unauthorized
    assert "login.html" in response.text
    assert "Please log in to access the dashboard" in response.text

    # Test authenticated access
    login_data = {"username": test_user["username"], "password": "testpassword"}
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/dashboard", headers=headers)
    assert response.status_code == 200
    assert "Dashboard" in response.text
