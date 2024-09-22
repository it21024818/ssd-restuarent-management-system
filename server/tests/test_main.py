import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_read_protected():
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}

def test_read_protected_with_token():
    token = "some_valid_token"
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, protected world!"}

def test_refresh_token():
    response = client.post("/refresh-token")
    assert response.status_code == 200