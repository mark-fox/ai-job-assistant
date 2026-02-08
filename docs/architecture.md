# AI Job Assistant – Architecture Overview

## 1. High-level overview

AI Job Assistant is a small full-stack application that helps a user:

- Store a basic user profile.
- Analyze a resume with an LLM-backed agent and store the summary.
- Generate interview answers based on stored resume analyses, job title, and company.
- View and delete stored resume analyses and answers.
- Inspect basic app and user metrics.

The stack is:

- **Frontend**: React + Vite + TypeScript + Tailwind CSS (single-page app)
- **Backend**: FastAPI + SQLAlchemy + Pydantic v2 + pytest
- **DB**: SQL database via SQLAlchemy (users, resume_analyses, interview_answers)
- **LLM provider**: OpenAI Responses API in production, stub provider in dev/tests

Authentication is stubbed using a custom `X-User-Id` header, resolved by
`get_current_user_optional`. This header is used to scope most list, metrics,
and delete operations to a “current user”.

---

## 2. System context

This diagram shows the main components and how they talk to each other.

```mermaid
flowchart LR
  user["User / Recruiter (Browser)"]
  frontend["Frontend SPA (React + Vite + TS)"]
  backend["Backend API (FastAPI)"]
  db["SQL DB: users, resume_analyses, interview_answers"]
  llm["LLM Provider (OpenAI or Stub)"]

  user --> frontend
  frontend --> backend
  backend --> db
  backend --> llm
```
---

## 3. Backend components

This diagram zooms into the FastAPI service and shows core routers, shared
dependencies, and external integrations.

```mermaid
flowchart LR
  subgraph Client
    spa["React SPA (Vite + TypeScript)"]
  end

  subgraph Backend["FastAPI Backend"]
    api_users["Users Router (/api/users/...)"]
    api_resume["Resume Router (/api/resume/...)"]
    api_answers["Answers Router (/api/generate/answer, /api/answers/...)"]
    api_metrics["Metrics Router (/api/metrics/...)"]
    status["Status Endpoint (/status)"]

    auth["get_current_user_optional (X-User-Id)"]
    agents["Job Assistant Agents (summarize_resume, generate_interview_answer)"]
    settings["Config & Settings (env, LLM provider)"]
    orm["SQLAlchemy ORM (Session + Models)"]
  end

  subgraph Data
    db["DB: users, resume_analyses, interview_answers"]
  end

  subgraph LLM
    llm_stub["Stub Provider"]
    llm_openai["OpenAI Responses API"]
  end

  spa --> status
  spa --> api_users
  spa --> api_resume
  spa --> api_answers
  spa --> api_metrics

  api_resume --> auth
  api_answers --> auth
  api_metrics --> auth

  api_resume --> agents
  api_answers --> agents

  api_users --> orm
  api_resume --> orm
  api_answers --> orm
  api_metrics --> orm
  orm --> db

  agents --> settings
  settings --> llm_stub
  settings --> llm_openai
```

Key points:

- **Routers**
  - `/api/users`: user creation and lookup.
  - `/api/resume`: resume analysis, listing, single fetch, answers-for-resume, delete.
  - `/api`: generate answer, list answers, get answer, delete answer.
  - `/api/metrics`: summary metrics and user-specific metrics.
  - `/status`: status and health information.
- **Shared dependencies**
  - `get_db` provides a SQLAlchemy session.
  - `get_current_user_optional` resolves the `X-User-Id` header into a `User | None`.

---

## 4. Request flow – Analyze Resume

This sequence diagram shows the end-to-end flow for
`POST /api/resume/analyze`.

```mermaid
sequenceDiagram
  participant U as User (Browser)
  participant FE as Frontend SPA
  participant API as FastAPI Backend
  participant AUTH as Auth Stub (get_current_user_optional)
  participant AG as summarize_resume Agent
  participant DB as Database

  U->>FE: Paste resume and click "Analyze resume"
  FE->>API: POST /api/resume/analyze { user_id, resume_text }
  API->>AUTH: Resolve X-User-Id header
  AUTH-->>API: current_user or None, or 401 if invalid

  API->>DB: Validate user_id if provided
  DB-->>API: User found or not found

  API->>AG: summarize_resume(resume_text)
  AG-->>API: summary_text and provider_used

  API->>DB: INSERT into resume_analyses (user_id, resume_text, summary)
  DB-->>API: New analysis id and created_at

  API-->>FE: 201 Created with id, user_id, summary, provider, created_at
  FE-->>U: Show summary and provider, then fetch answers for this resume
```

A similar flow applies for `POST /api/generate/answer`, where the backend:

1. Resolves the current user via `X-User-Id`.
2. Validates the `user_id` and optional `resume_analysis_id`.
3. Calls `generate_interview_answer` with question + job context + resume summary.
4. Writes an `InterviewAnswer` row and returns the created answer.

---

## 5. Auth stub and scoping model

Authentication is intentionally simplified for this project and is handled via
an `X-User-Id` header:

- `get_current_user_optional`:
  - Returns `None` if the header is not present.
  - Returns a `User` instance when the header contains a valid user id.
  - Returns HTTP 401 when the header is present but does not match an existing user.

Endpoints use this helper to implement consistent behavior:

- **Resume and answer creation**:
  - If both header user and body `user_id` are set and mismatch → 400.
  - If header user is set and `user_id` is missing → default `user_id` to header user id.
  - If header user is missing → rely on explicit `user_id` in the body.

- **List endpoints (`GET /api/resume`, `GET /api/answers`)**:
  - If both header user and query `user_id` are set and mismatch → 400.
  - If header user is set and query `user_id` is missing → filter by header user.
  - If no header user, but query `user_id` is present → filter by that user.
  - Otherwise → return all records (paginated).

- **Delete endpoints**:
  - Require a valid header user.
  - Only allow deleting records owned by that user (or unowned records).
  - Return 403 for attempts to delete another user’s data.

---

## 6. LLM provider modes

The backend supports two LLM provider modes, configured via settings:

- **Stub provider**:
  - Used in development and tests.
  - Returns deterministic, echo-style content.
  - Allows pytest to assert on generic properties (e.g. provider name) without
    depending on real LLM output.

- **OpenAI provider**:
  - Uses the OpenAI Responses API with `OPENAI_API_KEY` from environment.
  - Used in real deployments.
  - Tests do not assert on exact answer text when this provider is enabled.

The current provider name is exposed via the `/status` endpoint and included in
API responses where applicable.

---

## 7. Metrics and observability

Metrics endpoints:

- `GET /api/metrics/summary`:
  - Returns:
    - `total_users`
    - `total_resume_analyses`
    - `total_answers`
    - `user_resume_analyses` (only when `X-User-Id` is present)
    - `user_answers` (only when `X-User-Id` is present)

- `GET /api/metrics/user`:
  - Requires a valid `X-User-Id` header.
  - Returns:
    - `user_id`
    - `resume_analyses`
    - `answers`

Logging:

- Logs warnings and errors for:
  - Duplicate user creation attempts.
  - Missing users, resumes, and answers.
  - Mismatched header/body user ids.
  - Database failures when creating or deleting records.
- Logs info-level messages on successful user creation, resume analysis creation,
  answer generation, and deletes.

This combination of metrics and logging supports debugging, basic observability,
and future extension into a more complete monitoring stack.
