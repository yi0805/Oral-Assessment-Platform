# Project 20 — AI-Supported Oral Assessment API

Backend service for Project 20. Instructors upload course materials, AI generates oral assessment questions, students complete timed chat-based sessions, and instructors review AI-generated summaries before releasing grades.

## System overview

```
Instructor uploads PDF/PPTX  →  S3 (file storage)
                             →  RDS PostgreSQL (metadata + processing state)
                             →  Gemini embedding → pgvector (RAG search)

Student completes session    →  RDS (transcript, answers, timing)

AI summary generated         →  OpenRouter LLM → RDS (ai_summaries table)

Instructor releases grade    →  RDS (instructor_feedback table)
Student views results        →  RDS (read-only)
```

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Python 3.11 |
| ORM | SQLAlchemy 2.0 |
| Database | AWS RDS PostgreSQL 16 + pgvector |
| File storage | AWS S3 |
| Embeddings | Google Gemini `gemini-embedding-001` (768-dim) |
| LLM | OpenRouter free tier |
| Auth | Google OAuth 2.0 + JWT (python-jose) |
| Rate limiting | slowapi |

## Project structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/          # One file per resource group
│   │   │   ├── auth.py      # Google OAuth + dev-token
│   │   │   ├── courses.py   # Course CRUD + enrollment + CSV import
│   │   │   ├── materials.py # Upload, list, status, delete
│   │   │   ├── rubrics.py   # Rubric CRUD
│   │   │   ├── questions.py # Question pools + AI generation
│   │   │   ├── assessments.py # Assessment config + publish
│   │   │   ├── sessions.py  # Start, respond, complete, transcript
│   │   │   └── feedback.py  # AI summary + instructor feedback + release
│   │   └── router.py        # Mounts all routers under /api/v1
│   ├── core/
│   │   ├── config.py        # All settings from .env (pydantic-settings)
│   │   ├── database.py      # SQLAlchemy engine + get_db dependency
│   │   ├── dependencies.py  # get_current_user, require_instructor, require_enrollment
│   │   ├── limiter.py       # slowapi rate limiter instance
│   │   └── security.py      # JWT create/verify + role resolution
│   ├── models/              # SQLAlchemy ORM models (one per table group)
│   ├── schemas/             # Pydantic request/response schemas
│   │   └── pagination.py    # Generic Page[T] paginated response
│   ├── services/
│   │   ├── embedding_service.py   # Gemini embedding calls
│   │   ├── material_pipeline.py   # PDF/PPTX/DOCX extraction → chunk → embed
│   │   ├── question_generator.py  # OpenRouter question generation
│   │   ├── ai_summary_service.py  # OpenRouter post-session summary
│   │   ├── rag_search.py          # pgvector cosine similarity search
│   │   └── s3_client.py           # S3/local file upload/download/delete
│   └── main.py              # App factory, CORS, rate limiting, health endpoints
├── db/
│   └── migrations/
│       ├── 001_schema.sql         # Complete schema (all 14 tables) — run on fresh DB
│       └── 999_seed_dev_data.sql  # Dev seed data — local/test only, NOT production
├── tests/
│   ├── conftest.py          # DB fixtures, TestClient, auth helpers, AI mocks
│   ├── api/
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   ├── test_courses.py
│   │   ├── test_materials.py
│   │   └── test_materials_s3_upload.py
│   └── services/
│       └── test_material_pipeline.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Local development setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ with pgvector **or** Docker
- `psql` CLI

### 1. Create virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys (see section below)
```

### 3. Start a local PostgreSQL with pgvector (Docker)

```bash
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

### 4. Run the schema migration

```bash
psql -h localhost -U project20 -d project20_dev -f db/migrations/001_schema.sql
```

Optionally seed test data (1 instructor, 2 students, 1 course, 4 questions):

```bash
psql -h localhost -U project20 -d project20_dev -f db/migrations/999_seed_dev_data.sql
```

### 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health/db

### How to set up the sso aws s3 connection to backend code:

1. Install AWS CLI on Mac (M1): `brew install awscli`

   1. verify by: `brew install awscli` --> expected: `aws-cli/2.x.x`
2. After install, run: `aws configure sso`

   1. Fill things according to the aws account configaration:

      1. SSO start URL: https://uoa-sso.awsapps.com/start/#
      2. SSO region: ap-southeast-2
      3. give profile name → e.g. `uoa-sso`
3. Then login, `aws sso login --profile uoa-sso`(everytime before start backend)
4. if `aws s3 ls --profile uoa-sso` list the bucket `team8-project20-materials` == SUCCESS
5. Then connect to backend, by add code in `.env`:

   ```python
   STORAGE_BACKEND=s3
   AWS_PROFILE_NAME=uoa-sso
   AWS_REGION=ap-southeast-2
   S3_BUCKET_NAME=team8-project20-materials
   ```

6. Start the backend: ...

## AWS RDS setup (production / team shared DB)

### Connect to RDS

```bash
# Download SSL certificate (one-time)
curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

export RDSHOST="project20-db-pg16.cntu207sfdan.ap-southeast-2.rds.amazonaws.com"

# Test connection
psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem"
```

### Run migrations on RDS

```bash
# Schema only (production)
psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem" \
  -f db/migrations/001_schema.sql

# Verify all 14 tables exist
psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem" \
  -c "\dt"
```

Do **not** run `999_seed_dev_data.sql` on production.

### Point the backend at RDS

In `backend/.env`:

```bash
DATABASE_URL=postgresql://project20:PASSWORD@project20-db-pg16.cntu207sfdan.ap-southeast-2.rds.amazonaws.com:5432/postgres?sslmode=verify-full&sslrootcert=./global-bundle.pem
STORAGE_BACKEND=s3
S3_BUCKET_NAME=team8-project20-materials
AWS_REGION=ap-southeast-2
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `GEMINI_API_KEY` | ✅ | Google AI Studio key for embeddings |
| `OPENROUTER_API_KEY` | ✅ | OpenRouter key for LLM completions |
| `JWT_SECRET_KEY` | ✅ | Random secret for signing JWTs |
| `GOOGLE_CLIENT_ID` | OAuth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth | Google OAuth client secret |
| `STORAGE_BACKEND` | | `local` (default) or `s3` |
| `S3_BUCKET_NAME` | S3 | S3 bucket name for file uploads |
| `AWS_REGION` | S3 | AWS region (default: `ap-southeast-2`) |
| `AWS_ACCESS_KEY_ID` | S3 | AWS credentials (or use profile/instance role) |
| `AWS_SECRET_ACCESS_KEY` | S3 | AWS credentials |
| `CORS_ORIGINS` | | JSON array of allowed origins |
| `DEBUG` | | `true` enables dev-token endpoint and relaxed CORS |
| `FRONTEND_URL` | | SPA URL for OAuth redirect |

Generate a secure JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## API endpoints (49 total)

| Group | Prefix | Key endpoints |
|---|---|---|
| Health | `/` | `GET /`, `/health/db`, `/health/ai`, `/health/migrations` |
| Auth | `/api/v1/auth` | `POST /dev-token`, `GET /me`, Google OAuth |
| Courses | `/api/v1/courses` | CRUD, enroll, CSV bulk import |
| Materials | `/api/v1` | Upload PDF/PPTX/DOCX, list, status, delete |
| Rubrics | `/api/v1` | CRUD per course |
| Questions | `/api/v1` | Pool CRUD, AI generate, approve, publish |
| Assessments | `/api/v1` | Create, configure, publish |
| Sessions | `/api/v1` | Start, respond, complete, transcript, `/sessions/mine` |
| Feedback | `/api/v1` | AI summary, instructor feedback, release to student |

Full interactive docs at `/docs` (Swagger UI).

### Authentication in Swagger

1. `POST /api/v1/auth/dev-token` → `{"email": "you@test.com", "role": "instructor"}`
2. Copy the `access_token`
3. Click **🔒 Authorize** (top-right) → paste token → Authorize

## Running tests

Tests require a separate PostgreSQL database with pgvector:

```bash
# Create test database
createdb project20_test

# Run all tests
TEST_DATABASE_URL="postgresql://project20:localdev123@localhost:5432/project20_test" \
  pytest tests/ -v

# Run a specific file
TEST_DATABASE_URL="..." pytest tests/api/test_auth.py -v
```

Tests skip automatically if `TEST_DATABASE_URL` is not set. AI calls (Gemini, OpenRouter) are always mocked in tests.

## What is stored where

| Data | Storage |
|---|---|
| Uploaded files (PDF, PPTX, DOCX) | S3 (`local_uploads/` in dev) |
| Users, courses, enrollments | RDS `users`, `courses`, `course_enrollments` |
| Material metadata + processing state | RDS `materials` |
| Text chunks + 768-dim vectors | RDS `material_chunks` (pgvector) |
| Rubrics, question pools, questions | RDS `rubrics`, `question_pools`, `questions` |
| Assessment config | RDS `assessment_configs` |
| Session state + transcript | RDS `assessment_sessions`, `transcript_messages` |
| AI summary | RDS `ai_summaries` |
| Instructor grade + feedback | RDS `instructor_feedback` |

## Inspect RDS data via psql

```bash
# Row counts across all tables
psql "$DB_URL" -c "
SELECT 'users' AS t, COUNT(*) FROM users UNION ALL
SELECT 'courses',    COUNT(*) FROM courses UNION ALL
SELECT 'materials',  COUNT(*) FROM materials UNION ALL
SELECT 'material_chunks', COUNT(*) FROM material_chunks UNION ALL
SELECT 'assessment_sessions', COUNT(*) FROM assessment_sessions UNION ALL
SELECT 'transcript_messages', COUNT(*) FROM transcript_messages UNION ALL
SELECT 'ai_summaries', COUNT(*) FROM ai_summaries;
"

# Material processing status
psql "$DB_URL" -c "
SELECT title, processing_status, total_chunks FROM materials;
"
```

## Docker

```bash
# Build image
docker build -t project20-api .

# Run with docker-compose (starts PostgreSQL + API together)
docker compose up
```

The `docker-compose.yml` at the project root starts a local `pgvector/pgvector:pg15` database and the API with hot-reload.
