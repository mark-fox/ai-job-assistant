from fastapi.testclient import TestClient


def test_analyze_resume_and_generate_answer(client: TestClient):
    resume_text = (
        "Junior software engineer with experience building backend APIs. "
        "Skilled in Python, FastAPI, and SQL. Focused on learning AI engineering."
    )

    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": None,
            "resume_text": resume_text,
        },
    )
    assert resume_resp.status_code == 201
    resume_data = resume_resp.json()
    assert resume_data["id"] > 0
    assert "summary" in resume_data
    assert resume_data["provider"] in ("stub", "openai")

    analysis_id = resume_data["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": None,
            "resume_analysis_id": analysis_id,
            "question": "Tell me about yourself.",
            "job_title": "Junior AI Engineer",
            "company_name": "Example Corp",
        },
    )
    assert answer_resp.status_code == 201
    answer_data = answer_resp.json()
    assert answer_data["id"] > 0
    assert answer_data["resume_analysis_id"] == analysis_id
    
    # Behavior depends on provider: stub echoes the question text, OpenAI does not have to.
    if answer_data["provider"] == "stub":
        assert "Tell me about yourself." in answer_data["answer"]
    else:
        # For real AI answers, just require a non-trivial response.
        assert isinstance(answer_data["answer"], str)
        assert len(answer_data["answer"].strip()) > 20

    assert answer_data["provider"] in ("stub", "openai")


def test_generate_answer_validation_error(client: TestClient):
    short_question_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": None,
            "resume_analysis_id": None,
            "question": "Hi",
            "job_title": "Junior AI Engineer",
            "company_name": "Example Corp",
        },
    )
    assert short_question_resp.status_code == 422


def test_generate_answer_with_mismatched_user_and_resume(client: TestClient):
    user_resp = client.post(
        "/api/users",
        json={
            "email": "owner@example.com",
            "full_name": "Resume Owner",
        },
    )
    assert user_resp.status_code == 201
    owner = user_resp.json()
    owner_id = owner["id"]

    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": owner_id,
            "resume_text": (
                "Software engineer with experience in backend development. "
                "Comfortable with Python, FastAPI, and SQL databases."
            ),
        },
    )
    assert resume_resp.status_code == 201
    resume_data = resume_resp.json()
    analysis_id = resume_data["id"]

    other_user_resp = client.post(
        "/api/users",
        json={
            "email": "other@example.com",
            "full_name": "Other User",
        },
    )
    assert other_user_resp.status_code == 201
    other_user = other_user_resp.json()
    other_user_id = other_user["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": other_user_id,
            "resume_analysis_id": analysis_id,
            "question": "Why are you a good fit for this role?",
            "job_title": "Backend Engineer",
            "company_name": "Example Corp",
        },
    )

    assert answer_resp.status_code == 400
    data = answer_resp.json()
    assert data["detail"] == "Resume analysis does not belong to the specified user."


def test_list_resume_analyses(client: TestClient):
    resume_text = (
        "Backend engineer with experience in Python and FastAPI. "
        "Interested in AI and data-heavy applications."
    )

    create_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": None,
            "resume_text": resume_text,
        },
    )
    assert create_resp.status_code == 201

    list_resp = client.get("/api/resume?limit=10&offset=0")
    assert list_resp.status_code == 200

    items = list_resp.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    first = items[0]
    assert "id" in first
    assert "summary" in first
    assert first["provider"] in ("stub", "openai")


def test_list_answers(client: TestClient):
    resume_text = (
        "Software engineer with a focus on backend systems and testing. "
        "Comfortable with Python, FastAPI, and SQL."
    )

    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": None,
            "resume_text": resume_text,
        },
    )
    assert resume_resp.status_code == 201
    resume_data = resume_resp.json()
    analysis_id = resume_data["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": None,
            "resume_analysis_id": analysis_id,
            "question": "What interests you about backend development?",
            "job_title": "Backend Engineer",
            "company_name": "Example Corp",
        },
    )
    assert answer_resp.status_code == 201

    list_resp = client.get("/api/answers?limit=10&offset=0")
    assert list_resp.status_code == 200

    items = list_resp.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    first = items[0]
    assert "id" in first
    assert "answer" in first
    assert first["provider"] in ("stub", "openai")


def test_list_resume_analyses_filtered_by_user(client: TestClient):
    user1_resp = client.post(
        "/api/users",
        json={"email": "resume_user1@example.com", "full_name": "Resume User 1"},
    )
    assert user1_resp.status_code == 201
    user1_id = user1_resp.json()["id"]

    user2_resp = client.post(
        "/api/users",
        json={"email": "resume_user2@example.com", "full_name": "Resume User 2"},
    )
    assert user2_resp.status_code == 201
    user2_id = user2_resp.json()["id"]

    for i in range(2):
        resp = client.post(
            "/api/resume/analyze",
            json={
                "user_id": user1_id,
                "resume_text": (
                    f"Resume for user 1, entry {i}. Backend engineer with FastAPI and SQL."
                ),
            },
        )
        assert resp.status_code == 201

    resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user2_id,
            "resume_text": (
                "Resume for user 2. Focused on frontend development with React."
            ),
        },
    )
    assert resp.status_code == 201

    list_resp_user1 = client.get(f"/api/resume?user_id={user1_id}")
    assert list_resp_user1.status_code == 200
    items_user1 = list_resp_user1.json()
    assert len(items_user1) == 2
    assert all(item["user_id"] == user1_id for item in items_user1)

    list_resp_user2 = client.get(f"/api/resume?user_id={user2_id}")
    assert list_resp_user2.status_code == 200
    items_user2 = list_resp_user2.json()
    assert len(items_user2) == 1
    assert items_user2[0]["user_id"] == user2_id


def test_list_answers_filtered_by_user(client: TestClient):
    user1_resp = client.post(
        "/api/users",
        json={"email": "answer_user1@example.com", "full_name": "Answer User 1"},
    )
    assert user1_resp.status_code == 201
    user1_id = user1_resp.json()["id"]

    user2_resp = client.post(
        "/api/users",
        json={"email": "answer_user2@example.com", "full_name": "Answer User 2"},
    )
    assert user2_resp.status_code == 201
    user2_id = user2_resp.json()["id"]

    resume1_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user1_id,
            "resume_text": (
                "Resume for answer user 1. Backend developer experienced with APIs."
            ),
        },
    )
    assert resume1_resp.status_code == 201
    resume1_id = resume1_resp.json()["id"]

    resume2_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user2_id,
            "resume_text": (
                "Resume for answer user 2. Software engineer with mixed stack."
            ),
        },
    )
    assert resume2_resp.status_code == 201
    resume2_id = resume2_resp.json()["id"]

    for i in range(2):
        resp = client.post(
            "/api/generate/answer",
            json={
                "user_id": user1_id,
                "resume_analysis_id": resume1_id,
                "question": f"User 1 question {i}?",
                "job_title": "Backend Engineer",
                "company_name": "Example Corp",
            },
        )
        assert resp.status_code == 201

    resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": user2_id,
            "resume_analysis_id": resume2_id,
            "question": "User 2 question?",
            "job_title": "Full Stack Engineer",
            "company_name": "Sample Inc",
        },
    )
    assert resp.status_code == 201

    list_resp_user1 = client.get(f"/api/answers?user_id={user1_id}")
    assert list_resp_user1.status_code == 200
    items_user1 = list_resp_user1.json()
    assert len(items_user1) == 2
    assert all(item["user_id"] == user1_id for item in items_user1)

    list_resp_user2 = client.get(f"/api/answers?user_id={user2_id}")
    assert list_resp_user2.status_code == 200
    items_user2 = list_resp_user2.json()
    assert len(items_user2) == 1
    assert items_user2[0]["user_id"] == user2_id


def test_generate_answer_uses_header_user_when_body_missing(client: TestClient):
    user_resp = client.post(
        "/api/users",
        json={"email": "header_user@example.com", "full_name": "Header User"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user_id,
            "resume_text": (
                "Resume for header user. Backend developer working with FastAPI."
            ),
        },
    )
    assert resume_resp.status_code == 201
    resume_id = resume_resp.json()["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        headers={"X-User-Id": str(user_id)},
        json={
            "user_id": None,
            "resume_analysis_id": resume_id,
            "question": "How do you approach debugging backend issues?",
            "job_title": "Backend Engineer",
            "company_name": "Example Corp",
        },
    )
    assert answer_resp.status_code == 201
    data = answer_resp.json()
    assert data["user_id"] == user_id


def test_generate_answer_rejects_mismatched_header_and_body_user(client: TestClient):
    user1_resp = client.post(
        "/api/users",
        json={"email": "header_mismatch1@example.com", "full_name": "Header Mismatch 1"},
    )
    assert user1_resp.status_code == 201
    user1_id = user1_resp.json()["id"]

    user2_resp = client.post(
        "/api/users",
        json={"email": "header_mismatch2@example.com", "full_name": "Header Mismatch 2"},
    )
    assert user2_resp.status_code == 201
    user2_id = user2_resp.json()["id"]

    answer_resp = client.post(
        "/api/generate/answer",
        headers={"X-User-Id": str(user1_id)},
        json={
            "user_id": user2_id,
            "resume_analysis_id": None,
            "question": "Why do you want this role?",
            "job_title": "Backend Engineer",
            "company_name": "Example Corp",
        },
    )
    assert answer_resp.status_code == 400
    data = answer_resp.json()
    assert data["detail"] == "Body user_id does not match authenticated user."


def test_list_answers_for_specific_resume(client: TestClient):
    # Create a user
    user_resp = client.post(
        "/api/users",
        json={"email": "resume_answers@example.com", "full_name": "Resume Answers User"},
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    # Create a resume analysis for that user
    resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user_id,
            "resume_text": (
                "Backend developer with experience in Python and FastAPI. "
                "Worked on internal tools and APIs for data-heavy features."
            ),
        },
    )
    assert resume_resp.status_code == 201
    resume_data = resume_resp.json()
    analysis_id = resume_data["id"]

    # Generate two answers tied to that resume
    for i in range(2):
        answer_resp = client.post(
            "/api/generate/answer",
            json={
                "user_id": user_id,
                "resume_analysis_id": analysis_id,
                "question": f"Question {i}?",
                "job_title": "Backend Engineer",
                "company_name": "Example Corp",
            },
        )
        assert answer_resp.status_code == 201

    # Generate an answer for a different resume so we can confirm filtering
    other_resume_resp = client.post(
        "/api/resume/analyze",
        json={
            "user_id": user_id,
            "resume_text": (
                "Different resume for filtering test. Focused on other projects."
            ),
        },
    )
    assert other_resume_resp.status_code == 201
    other_analysis_id = other_resume_resp.json()["id"]

    other_answer_resp = client.post(
        "/api/generate/answer",
        json={
            "user_id": user_id,
            "resume_analysis_id": other_analysis_id,
            "question": "Unrelated question?",
            "job_title": "Backend Engineer",
            "company_name": "Other Corp",
        },
    )
    assert other_answer_resp.status_code == 201

    # Now fetch answers just for the first resume analysis
    list_resp = client.get(f"/api/resume/{analysis_id}/answers?limit=10&offset=0")
    assert list_resp.status_code == 200

    items = list_resp.json()
    assert isinstance(items, list)
    # Should only include the 2 answers tied to this resume
    assert len(items) == 2
    assert all(item["resume_analysis_id"] == analysis_id for item in items)
    assert all(item["provider"] in ("stub", "openai") for item in items)
