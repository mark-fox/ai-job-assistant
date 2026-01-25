# AI Job Assistant

AI Job Assistant is a small full-stack application focused on a strong backend for analyzing resumes and generating interview answers. The backend exposes HTTP APIs that store users, resume analyses, and interview answers. An agent layer sits between the API and the language model provider and controls how summaries and answers are produced.

The frontend is a thin React UI that calls these APIs and surfaces backend-driven metadata such as environment, provider, and database status.

---

## Tech Stack

**Backend**

- Python
- FastAPI
- SQLAlchemy
- Pydantic v2
- SQLite (local development)
- pytest

**Frontend**

- React
- Vite
- TypeScript
- Tailwind CSS

---

## Repository Structure

```text
ai-job-assistant/
  backend/
    app/
      api/
        answers.py       # Interview answer endpoints
        resume.py        # Resume analysis endpoints
        users.py         # User endpoints
      agents/
        job_assistant.py # Agent logic and LLM provider routing
      core/
        config.py        # Settings and environment configuration
        db.py            # Database engine and session management
        logging.py       # Logging setup
      models/
        answer.py        # InterviewAnswer ORM model
        resume.py        # ResumeAnalysis ORM model
        user.py          # User ORM model
      schemas/
        answer.py        # Request/response models for answers
        resume.py        # Request/response models for resumes
        user.py          # Request/response models for users
      main.py            # FastAPI app, routing, and health endpoint
    tests/
      conftest.py        # Test database and TestClient setup
      test_status.py
      test_users.py
      test_resume_and_answers.py
    requirements.txt
  frontend/
    src/
      App.tsx            # Main UI layout and API integration
      config.ts          # API base URL configuration
      main.tsx
      index.css
    vite.config.ts
    package.json
```

---

## Backend Architecture

### Settings and Configuration

`app/core/config.py` centralizes configuration via a `Settings` dataclass. Values are loaded from environment variables:

- `APP_ENV` – application environment (default: `development`)
- `DATABASE_URL` – SQLAlchemy database URL (default: `sqlite:///./ai_job_assistant.db`)
- `LOG_LEVEL` – logging level (default: `INFO`)
- `LOG_DIR` – directory for log files (default: `logs`)
- `LLM_PROVIDER` – language model provider (`stub` or `openai`, default: `stub`)
- `OPENAI_API_KEY` – optional API key for the OpenAI provider
- `OPENAI_MODEL` – model name for the OpenAI provider (default: `gpt-4o-mini`)

`app/core/logging.py` configures application logging and is imported by the FastAPI app and other modules.

### Database and Models

`app/core/db.py` provides:

- A SQLAlchemy engine bound to `DATABASE_URL`
- A session factory (`SessionLocal`)
- A `Base` class for ORM models

ORM models:

- `User`
  - `id` (PK)
  - `email` (unique)
  - `full_name`
  - `created_at`
- `ResumeAnalysis`
  - `id` (PK)
  - `user_id` (FK to `User.id`, nullable)
  - `resume_text`
  - `summary`
  - `created_at`
- `InterviewAnswer`
  - `id` (PK)
  - `user_id` (FK to `User.id`, nullable)
  - `resume_analysis_id` (FK to `ResumeAnalysis.id`, nullable)
  - `question`
  - `job_title` (nullable)
  - `company_name` (nullable)
  - `answer`
  - `created_at`

### Schemas and Validation

Pydantic v2 models live under `app/schemas/`:

- `UserCreate`, `UserRead`
- `ResumeAnalyzeRequest`, `ResumeAnalysisRead`
  - `resume_text` enforces a minimum length of 20 characters
- `GenerateAnswerRequest`, `InterviewAnswerRead`
  - `question` enforces a minimum length of 5 characters

Read models use `ConfigDict(from_attributes=True)` and are used as `response_model`s in FastAPI routes.

---

## Agent Layer

`app/agents/job_assistant.py` defines the agent interface and provider routing.

- `LLMProvider` enum:
  - `stub`
  - `openai`
- Public functions:
  - `summarize_resume(resume_text: str) -> str`
  - `generate_interview_answer(question: str, job_title: Optional[str], company_name: Optional[str]) -> str`

Provider selection:

- `LLM_PROVIDER=stub`
  - Uses `_summarize_resume_stub` and `_generate_interview_answer_stub`
  - Summaries include basic counts such as word and line count
  - Answers echo the question, job title, company name, and indicate development placeholder behavior
- `LLM_PROVIDER=openai`
  - Uses `_summarize_resume_openai` and `_generate_interview_answer_openai`
  - If `OPENAI_API_KEY` is not set, logs a warning and falls back to stub behavior
  - Logs model and context information when the provider is configured

This layer keeps model-specific logic out of the API handlers and makes provider switching explicit.

---

## API Overview

### Health and Status

#### `GET /status`

Returns overall service status and health checks.

Example response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "llm_provider": "stub",
  "checks": {
    "database": "ok"
  }
}
```

### Users

#### `POST /api/users`

Create a user.

Request body:

```json
{
  "email": "user@example.com",
  "full_name": "User Name"
}
```

Response `201 Created`:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  "created_at": "2025-01-01T12:00:00Z"
}
```

Errors:

- `400` if the email already exists

#### `GET /api/users/{user_id}`

Fetch a user by ID.

### Resume Analysis

#### `POST /api/resume/analyze`

Analyze resume text and store the result.

Request body:

```json
{
  "user_id": 1,
  "resume_text": "Longer resume text with at least twenty characters..."
}
```

Response `201 Created`:

```json
{
  "id": 1,
  "user_id": 1,
  "resume_text": "Longer resume text with at least twenty characters...",
  "summary": "Basic analysis only. Approximate word count: 12. Non-empty line count: 3.",
  "created_at": "2025-01-01T12:00:00Z",
  "provider": "stub"
}
```

Validation and errors:

- `422` if `resume_text` is shorter than 20 characters
- `404` if a non-null `user_id` does not reference an existing user

#### `GET /api/resume`

List resume analyses with pagination and optional user filter.

Query parameters:

- `limit` (default 20, max 100)
- `offset` (default 0)
- `user_id` (optional)

#### `GET /api/resume/{analysis_id}`

Fetch a single resume analysis by ID.

### Interview Answers

#### `POST /api/generate/answer`

Generate and store an interview answer.

Request body:

```json
{
  "user_id": 1,
  "resume_analysis_id": 1,
  "question": "Tell me about yourself.",
  "job_title": "Junior AI Engineer",
  "company_name": "Example Corp"
}
```

Response `201 Created`:

```json
{
  "id": 1,
  "user_id": 1,
  "resume_analysis_id": 1,
  "question": "Tell me about yourself.",
  "job_title": "Junior AI Engineer",
  "company_name": "Example Corp",
  "answer": "Question: Tell me about yourself. | Target role: Junior AI Engineer | Company: Example Corp | This is a placeholder answer for development purposes, not a final AI-generated response.",
  "created_at": "2025-01-01T12:00:00Z",
  "provider": "stub"
}
```

Validation and errors:

- `422` if `question` is shorter than 5 characters
- `404` if `user_id` is provided and does not reference an existing user
- `404` if `resume_analysis_id` is provided and does not reference an existing resume analysis
- `400` if both `user_id` and `resume_analysis_id` are provided and the resume analysis belongs to a different user

#### `GET /api/answers`

List interview answers with pagination and optional user filter.

Query parameters:

- `limit` (default 20, max 100)
- `offset` (default 0)
- `user_id` (optional)

#### `GET /api/answers/{answer_id}`

Fetch a single interview answer by ID.

---

## Frontend Overview

The frontend lives under `frontend/` and provides a minimal UI for:

- Pasting a resume and sending it to `POST /api/resume/analyze`
- Entering an interview question, job title, and company name and sending it to `POST /api/generate/answer`
- Displaying backend-driven metadata from `GET /status` in the header:
  - Environment
  - LLM provider
  - Database status
- Displaying the `provider` field returned by the backend under the resume summary and generated answer

The frontend treats the backend as the source of truth for validation errors, status, and provider information.

---

## Running the Backend

### Prerequisites

- Python 3.11+
- `pip`

### Setup

From the `backend/` directory:

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\\Scripts\\activate   # Windows PowerShell

pip install -r requirements.txt
```

### Environment Variables

Example `.env` for local development:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./ai_job_assistant.db
LOG_LEVEL=INFO
LOG_DIR=logs
LLM_PROVIDER=stub
# OPENAI_API_KEY=...
# OPENAI_MODEL=gpt-4o-mini
```

Set variables in the shell or via a `.env` loader if configured.

### Start the API

From `backend/` with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

---

## Running the Frontend

From the `frontend/` directory:

```bash
npm install
npm run dev
```

The app runs at `http://127.0.0.1:5173` by default and sends requests to `http://127.0.0.1:8000` when `VITE_API_BASE_URL` is not set.

To override the backend URL, set `VITE_API_BASE_URL` in a Vite environment file (for example `.env.local`).

---

## Testing

The backend includes automated tests using `pytest`.

Tests use a separate SQLite database file and a `TestClient` fixture.

From the `backend/` directory:

```bash
pytest
```

The test suite covers:

- Service status and health endpoint
- User creation and retrieval
- Resume analysis creation, listing, and retrieval
- Interview answer creation, listing, and retrieval
- Validation errors for invalid questions and resumes
- Consistency checks between users and resume analyses
- User-specific filtering of resume analyses and interview answers
