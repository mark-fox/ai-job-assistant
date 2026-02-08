# AI Job Assistant

AI Job Assistant is a small full-stack application focused on a strong backend for analyzing resumes and generating interview answers. The backend exposes HTTP APIs that store users, resume analyses, and interview answers. An agent layer sits between the API and the language model provider and controls how summaries and answers are produced.

The frontend is a thin React UI that calls these APIs and surfaces backend-driven metadata such as environment, provider, and database status.

A simple auth stub using the `X-User-Id` header simulates per-user behavior. List, metrics, and delete endpoints are scoped based on this header.

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
        answers.py         # Interview answer endpoints (generate, list, get, delete)
        resume.py          # Resume analysis endpoints (analyze, list, get, answers-for-resume, delete)
        users.py           # User endpoints
        metrics.py         # Metrics endpoints (totals + per-user)
      agents/
        job_assistant.py   # Agent logic and LLM provider routing
      core/
        auth.py            # X-User-Id auth stub
        config.py          # Settings and environment configuration
        db.py              # Database engine and session management
        logging_config.py  # Logging setup
      models/
        interview_answer.py  # InterviewAnswer ORM model
        resume_analysis.py   # ResumeAnalysis ORM model
        user.py              # User ORM model
      schemas/
        answer.py          # Request/response models for answers
        resume.py          # Request/response models for resumes
        user.py            # Request/response models for users
        main.py            # Schema re-exports for convenience
      main.py              # FastAPI app, routing, and status endpoint
    logs/                  # Log files (created at runtime)
    tests/
      conftest.py                  # Test database and TestClient setup
      test_status.py               # /status endpoint tests
      test_users.py                # User endpoints
      test_resume_and_answers.py   # Resume + answer endpoints and auth behavior
      test_metrics.py              # Metrics endpoints
    requirements.txt
  frontend/
    src/
      App.tsx              # Main UI layout and API integration
      config.ts            # API base URL configuration
      main.tsx
      index.css
      assets/              # CSS and static assets
    vite.config.ts
    package.json
  docs/
    architecture.md        # Mermaid diagrams and architecture overview
```

---

## Backend Architecture

### Settings and Configuration

`app/core/config.py` centralizes configuration via a Pydantic `Settings` class. Values are loaded from environment variables:

- `APP_ENV` – application environment (default: `development`)
- `DATABASE_URL` – SQLAlchemy database URL (default: `sqlite:///./ai_job_assistant.db`)
- `LOG_LEVEL` – logging level (default: `INFO`)
- `LOG_DIR` – directory for log files (default: `logs`)
- `LLM_PROVIDER` – language model provider (`stub` or `openai`, default: `stub`)
- `OPENAI_API_KEY` – optional API key for the OpenAI provider
- `OPENAI_MODEL` – model name for the OpenAI provider (for example `gpt-4o-mini`)

`app/core/logging_config.py` configures application logging and is imported by the FastAPI app and other modules.

### Database and Models

`app/core/db.py` provides:

- A SQLAlchemy engine bound to `DATABASE_URL`
- A session factory (`SessionLocal`)
- A `Base` class for ORM models

ORM models:

- `User` (`app/models/user.py`)
  - `id` (PK)
  - `email` (unique)
  - `full_name`
  - `created_at`
- `ResumeAnalysis` (`app/models/resume_analysis.py`)
  - `id` (PK)
  - `user_id` (FK to `User.id`, nullable)
  - `resume_text`
  - `summary`
  - `created_at`
- `InterviewAnswer` (`app/models/interview_answer.py`)
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

### Auth Stub and User Scoping

`app/core/auth.py` defines `get_current_user_optional`, which resolves the `X-User-Id` header into a `User | None`:

- Returns `None` when `X-User-Id` is not provided.
- Returns a `User` when the header contains a valid user id.
- Raises `401 Unauthorized` when the header is present but does not match an existing user.

Endpoints use this helper for consistent behavior:

- For create endpoints (`/api/resume/analyze`, `/api/generate/answer`):
  - If both header user and body `user_id` are present and do not match → `400 Bad Request`.
  - If header user is present and body `user_id` is `null` → use the header user id.
- For list endpoints (`GET /api/resume`, `GET /api/answers`):
  - If both header user and query `user_id` are present and do not match → `400 Bad Request`.
  - If header user is present and `user_id` query is missing → results are scoped to the header user.
  - If no header user but `user_id` query is present → filter by that user.
  - Otherwise → return all records (paginated).
- For delete endpoints:
  - Header user is required.
  - A user can delete their own records (or unowned records), but receives `403 Forbidden` when attempting to delete another user’s data.

---

## Agent Layer

`app/agents/job_assistant.py` defines the agent interface and provider routing.

- `LLMProvider` enum:
  - `stub`
  - `openai`
- Public functions:
  - `summarize_resume(resume_text: str) -> tuple[str, str]`
  - `generate_interview_answer(question: str, job_title: Optional[str], company_name: Optional[str], resume_summary: Optional[str]) -> tuple[str, str]`

Each function returns a pair of `(text, provider_used)` so that API responses can include the provider used for that operation.

Provider selection:

- `LLM_PROVIDER=stub`
  - Uses deterministic stub functions for summaries and answers.
  - Summaries and answers are simple, predictable text suitable for tests.
- `LLM_PROVIDER=openai`
  - Uses the OpenAI Responses API.
  - If `OPENAI_API_KEY` is not set, logs a warning and falls back to stub behavior.
  - Tests do not assert on the exact answer text when this provider is in use.

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

---

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

---

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

Response `201 Created` (shape):

```json
{
  "id": 1,
  "user_id": 1,
  "resume_text": "Longer resume text with at least twenty characters...",
  "summary": "Stub or OpenAI-generated summary text...",
  "created_at": "2025-01-01T12:00:00Z",
  "provider": "stub"
}
```

Validation and errors:

- `422` if `resume_text` is shorter than 20 characters
- `404` if a non-null `user_id` does not reference an existing user
- `400` if header user and body `user_id` are both present and do not match

#### `GET /api/resume`

List resume analyses with pagination and optional user filter.

Query parameters:

- `limit` (default 20, max 100)
- `offset` (default 0)
- `user_id` (optional)

Response items include a `provider` field derived from the currently configured LLM provider.

#### `GET /api/resume/{analysis_id}`

Fetch a single resume analysis by ID.

#### `GET /api/resume/{analysis_id}/answers`

List interview answers associated with a specific resume analysis, ordered by `created_at` descending.

Query parameters:

- `limit` (default 20, max 100)
- `offset` (default 0)

#### `DELETE /api/resume/{analysis_id}`

Delete a resume analysis.

- Requires a valid `X-User-Id` header.
- The current user can delete:
  - Analyses they own (`user_id` matches the header), or
  - Analyses with `user_id == null`.
- Returns `204 No Content` on success.
- Returns `404` if the resume analysis does not exist.
- Returns `403` if the resume analysis belongs to a different user.

---

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

Response `201 Created` (shape):

```json
{
  "id": 1,
  "user_id": 1,
  "resume_analysis_id": 1,
  "question": "Tell me about yourself.",
  "job_title": "Junior AI Engineer",
  "company_name": "Example Corp",
  "answer": "Stub or OpenAI-generated answer text...",
  "created_at": "2025-01-01T12:00:00Z",
  "provider": "stub"
}
```

Behavior:

- If `resume_analysis_id` is provided and valid, the agent receives the stored resume summary as context.
- The created answer is stored in the `interview_answers` table.

Validation and errors:

- `422` if `question` is shorter than 5 characters
- `404` if `user_id` is provided and does not reference an existing user
- `404` if `resume_analysis_id` is provided and does not reference an existing resume analysis
- `400` if both `user_id` and `resume_analysis_id` are provided and the resume analysis belongs to a different user
- `400` if header user and body `user_id` are both present and do not match

#### `GET /api/answers`

List interview answers with pagination and optional user filter.

Query parameters:

- `limit` (default 20, max 100)
- `offset` (default 0)
- `user_id` (optional)

Response items include a `provider` field derived from the currently configured LLM provider.

#### `GET /api/answers/{answer_id}`

Fetch a single interview answer by ID.

#### `DELETE /api/answers/{answer_id}`

Delete an interview answer.

- Requires a valid `X-User-Id` header.
- The current user can delete:
  - Answers they own (`user_id` matches the header), or
  - Answers with `user_id == null`.
- Returns `204 No Content` on success.
- Returns `404` if the answer does not exist.
- Returns `403` if the answer belongs to a different user.

---

### Metrics

#### `GET /api/metrics/summary`

Returns global and optional per-user metrics.

Response shape:

```json
{
  "total_users": 3,
  "total_resume_analyses": 10,
  "total_answers": 25,
  "user_resume_analyses": 4,
  "user_answers": 12
}
```

Behavior:

- Without `X-User-Id`, only the `total_*` fields are populated; `user_resume_analyses` and `user_answers` are `null`.
- With a valid `X-User-Id`, the `user_*` fields are populated for that user.

#### `GET /api/metrics/user`

Requires a valid `X-User-Id` header and returns metrics specific to that user:

```json
{
  "user_id": 1,
  "resume_analyses": 4,
  "answers": 12
}
```

---

## Frontend Overview

The frontend lives under `frontend/` and provides a minimal UI for:

- Pasting a resume and sending it to `POST /api/resume/analyze`.
- Entering an interview question, job title, and company name and sending it to `POST /api/generate/answer`.
- Displaying backend-driven metadata from `GET /status` in the header:
  - Environment
  - LLM provider
  - Database status
- Displaying the `provider` field returned by the backend under the resume summary and generated answer.
- Showing “Answers for this resume” as a scrollable list:
  - Each card shows the stored question, a truncated answer, provider, and created timestamp.
  - Clicking a card pulls that answer back into the main “Generated answer” display and repopulates the question field.

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
.venv\Scripts\Activate.ps1 # Windows PowerShell

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

- Service status and health endpoint.
- User creation, duplicate email handling, and retrieval.
- Resume analysis creation, listing, retrieval, and scoping by user and header.
- Interview answer generation, listing, retrieval, and scoping by user and header.
- Validation errors for invalid questions and resumes.
- Consistency checks between users and resume analyses (including mismatched user/resume cases).
- `X-User-Id` auth stub behavior (header vs body/query conflicts and defaults).
- Metrics endpoints (`/api/metrics/summary`, `/api/metrics/user`) with and without a header user.
- Delete behavior for resumes and answers (happy path, not found, and forbidden cases).
