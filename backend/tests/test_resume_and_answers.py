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
