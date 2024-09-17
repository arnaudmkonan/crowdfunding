from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import pytest
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_user(test_db):
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_read_users(test_db):
    # Create a user first
    client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["username"] == "testuser"

def test_create_project(test_db):
    # Create a user first
    user_response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    user_id = user_response.json()["id"]

    response = client.post(
        "/projects/",
        json={
            "title": "Test Project",
            "description": "This is a test project",
            "goal_amount": 1000.0,
            "creator_id": user_id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["description"] == "This is a test project"
    assert data["goal_amount"] == 1000.0
    assert data["creator"]["id"] == user_id

def test_read_projects(test_db):
    # Create a user and a project first
    user_response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    user_id = user_response.json()["id"]

    client.post(
        "/projects/",
        json={
            "title": "Test Project",
            "description": "This is a test project",
            "goal_amount": 1000.0,
            "creator_id": user_id
        }
    )

    response = client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Project"

def test_fund_project(test_db):
    # Create a user and a project first
    user_response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"}
    )
    user_id = user_response.json()["id"]

    project_response = client.post(
        "/projects/",
        json={
            "title": "Test Project",
            "description": "This is a test project",
            "goal_amount": 1000.0,
            "creator_id": user_id
        }
    )
    project_id = project_response.json()["id"]

    response = client.put(f"/projects/{project_id}/fund?amount=500.0")
    assert response.status_code == 200
    data = response.json()
    assert data["current_amount"] == 500.0
