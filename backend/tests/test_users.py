from fastapi.testclient import TestClient


def test_create_and_get_user(client: TestClient):
    create_resp = client.post(
        "/api/users",
        json={
            "email": "test_user@example.com",
            "full_name": "Test User",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["id"] > 0
    assert created["email"] == "test_user@example.com"
    assert created["full_name"] == "Test User"

    user_id = created["id"]

    get_resp = client.get(f"/api/users/{user_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == user_id
    assert fetched["email"] == "test_user@example.com"


def test_create_user_duplicate_email(client: TestClient):
    email = "duplicate_user@example.com"

    first = client.post(
        "/api/users",
        json={"email": email, "full_name": "First User"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/users",
        json={"email": email, "full_name": "Second User"},
    )
    assert second.status_code == 400
    data = second.json()
    assert data["detail"] == "User with this email already exists."
