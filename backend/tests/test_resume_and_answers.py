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
    assert resume_data["provider"] == "stub"

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
    assert "Tell me about yourself." in answer_data["answer"]
    assert answer_data["provider"] == "stub"

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
