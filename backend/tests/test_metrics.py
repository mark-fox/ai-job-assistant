from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_metrics_summary_without_user_header():
    # Create some data to count
    user_resp = client.post(
        "/api/users",
        json={"email": "metrics@example.com", "full_name": "Metrics User"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user_id,
            "resume_text": (
                "Backend dev with experience in Python and FastAPI. "
                "Worked on internal tools and APIs."
            ),
        },
    )
    assert resume_resp.status_code == 201
    analysis_id = resume_resp.json()["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": user_id,
            "resume_analysis_id": analysis_id,
            "question": "Tell me about yourself.",
            "job_title": "Backend Engineer",
            "company_name": "Example Corp",
        },
    )
    assert answer_resp.status_code == 201

    # Now call metrics summary without any header
    metrics_resp = client.get("/api/metrics/summary")
    assert metrics_resp.status_code == 200

    data = metrics_resp.json()
    assert "total_users" in data
    assert "total_resume_analyses" in data
    assert "total_answers" in data

    assert data["total_users"] >= 1
    assert data["total_resume_analyses"] >= 1
    assert data["total_answers"] >= 1

    # Per-user fields should be null when no header user is provided
    assert data["user_resume_analyses"] is None
    assert data["user_answers"] is None


def test_metrics_summary_with_header_user():
    # Create two users
    user1_resp = client.post(
        "/api/users",
        json={"email": "metrics_user1@example.com", "full_name": "Metrics User 1"},
    )
    assert user1_resp.status_code == 201
    user1_id = user1_resp.json()["id"]

    user2_resp = client.post(
        "/api/users",
        json={"email": "metrics_user2@example.com", "full_name": "Metrics User 2"},
    )
    assert user2_resp.status_code == 201
    user2_id = user2_resp.json()["id"]

    # User 1: one resume, two answers
    resume1_resp = client.post(
        "/api/resume/analyze",
        headers={"X-User-Id": str(user1_id)},
        json={
            "user_id": user1_id,
            "resume_text": (
                "User 1 resume - Backend developer with Python and FastAPI."
            ),
        },
    )
    assert resume1_resp.status_code == 201
    resume1_id = resume1_resp.json()["id"]

    for i in range(2):
        answer_resp = client.post(
            "/api/generate/answer",
            headers={"X-User-Id": str(user1_id)},
            json={
                "user_id": user1_id,
                "resume_analysis_id": resume1_id,
                "question": f"User 1 question {i}?",
                "job_title": "Backend Engineer",
                "company_name": "Example Corp",
            },
        )
        assert answer_resp.status_code == 201

    # User 2: one resume, one answer
    resume2_resp = client.post(
        "/api/resume/analyze",
        headers={"X-User-Id": str(user2_id)},
        json={
            "user_id": user2_id,
            "resume_text": (
                "User 2 resume - Backend developer focused on different stack."
            ),
        },
    )
    assert resume2_resp.status_code == 201
    resume2_id = resume2_resp.json()["id"]

    answer2_resp = client.post(
        "/api/generate/answer",
        headers={"X-User-Id": str(user2_id)},
        json={
            "user_id": user2_id,
            "resume_analysis_id": resume2_id,
            "question": "User 2 question?",
            "job_title": "Backend Engineer",
            "company_name": "Other Corp",
        },
    )
    assert answer2_resp.status_code == 201

    # Metrics for user 1
    metrics_resp = client.get(
        "/api/metrics/summary",
        headers={"X-User-Id": str(user1_id)},
    )
    assert metrics_resp.status_code == 200

    data = metrics_resp.json()
    assert data["user_resume_analyses"] == 1
    assert data["user_answers"] == 2

    # Totals should include both users' data
    assert data["total_users"] >= 2
    assert data["total_resume_analyses"] >= 2
    assert data["total_answers"] >= 3


def test_user_metrics_requires_auth():
    resp = client.get("/api/metrics/user")
    assert resp.status_code == 401
    data = resp.json()
    assert data["detail"] == "Authentication required to fetch user metrics."


def test_user_metrics_counts_for_user_with_data():
    # Create a user
    user_resp = client.post(
        "/api/users",
        json={"email": "user_metrics1@example.com", "full_name": "User Metrics 1"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    # Create a resume analysis for that user
    resume_resp = client.post(
        "/api/resume/analyze",
        headers={"X-User-Id": str(user_id)},
        json={
            "user_id": user_id,
            "resume_text": (
                "Resume for user metrics test. Backend dev with FastAPI and SQL."
            ),
        },
    )
    assert resume_resp.status_code == 201
    resume_id = resume_resp.json()["id"]

    # Create two answers for that user and resume
    for i in range(2):
        answer_resp = client.post(
            "/api/generate/answer",
            headers={"X-User-Id": str(user_id)},
            json={
                "user_id": user_id,
                "resume_analysis_id": resume_id,
                "question": f"Metrics question {i}?",
                "job_title": "Backend Engineer",
                "company_name": "Example Corp",
            },
        )
        assert answer_resp.status_code == 201

    # Fetch user metrics
    metrics_resp = client.get(
        "/api/metrics/user",
        headers={"X-User-Id": str(user_id)},
    )
    assert metrics_resp.status_code == 200

    data = metrics_resp.json()
    assert data["user_id"] == user_id
    assert data["resume_analyses"] == 1
    assert data["answers"] == 2


def test_user_metrics_counts_for_user_with_no_data():
    # Create a user with no resumes or answers
    user_resp = client.post(
        "/api/users",
        json={"email": "user_metrics_empty@example.com", "full_name": "User Metrics Empty"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    metrics_resp = client.get(
        "/api/metrics/user",
        headers={"X-User-Id": str(user_id)},
    )
    assert metrics_resp.status_code == 200

    data = metrics_resp.json()
    assert data["user_id"] == user_id
    assert data["resume_analyses"] == 0
    assert data["answers"] == 0