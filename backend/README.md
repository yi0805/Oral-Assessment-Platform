# Project 20 Backend

AI-supported oral assessment API for Project 20. Instructors upload course materials, AI generates oral assessment questions, students complete timed chat-based sessions, and instructors review AI-generated summaries before releasing grades.

## System Overview

```text
Instructor uploads PDF/PPTX/DOCX
  -> S3 or local storage
  -> PostgreSQL metadata + processing state
  -> Gemini embedding -> pgvector for RAG search

Student completes assessment session
  -> PostgreSQL transcript, answers, timing

AI summary generated
  -> OpenRouter LLM
  -> PostgreSQL ai_summaries table

Instructor releases grade
  -> PostgreSQL instructor_feedback table
Student views released results
  -> read-only API access
```

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Python 3.11 |
| ORM | SQLAlchemy 2.0 |
| Database | AWS RDS PostgreSQL 16 + pgvector |
| File storage | AWS S3 |
| Embeddings | Google Gemini `gemini-embedding-001` (768-dim) |
| LLM | OpenRouter free tier |
| Auth | Google OAuth 2.0 + JWT (`python-jose`) |
| Rate limiting | `slowapi` |

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── courses.py
│   │   │   ├── materials.py
│   │   │   ├── rubrics.py
│   │   │   ├── questions.py
│   │   │   ├── assessments.py
│   │   │   ├── sessions.py
│   │   │   └── feedback.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── limiter.py
│   │   └── security.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── material_pipeline.py
│   │   ├── question_generator.py
│   │   ├── ai_summary_service.py
│   │   ├── rag_search.py
│   │   └── s3_client.py
│   └── main.py
├── db/
│   └── migrations/
│       ├── 001_schema.sql
│       └── 999_seed_dev_data.sql
├── tests/
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Quick Start

These setup steps support both macOS and Windows. Commands are labeled when they differ by platform.

## Choose Your Setup First

Before starting, decide which environment you are using. Docker and AWS are not the same thing in this project.

| Option | What it uses | When to use it | What you need |
|---|---|---|---|
| Local development with Docker | Local PostgreSQL container on your own machine | Best for day-to-day backend development, debugging, and running tests safely | Docker Desktop, local `.env`, local DB schema |
| Local backend + AWS services | Backend runs on your machine, but uses shared AWS RDS and/or S3 | Use when you need shared team data or shared uploaded files | AWS access, RDS certificate, SSO login, AWS-related `.env` values |
| Full Docker Compose stack | Local PostgreSQL plus local backend container | Good when you want the backend and database both containerized locally | Docker Desktop and `docker compose up` |

### Important distinction

- Docker means services run locally on your computer
- AWS means services run remotely in the team or production cloud environment
- You do not need AWS just to run the backend locally
- You do not need Docker in order to connect your local backend to AWS RDS or AWS S3
- The most common beginner setup is: backend runs locally, database runs locally in Docker, storage stays local

### Recommended default for most team members

Use local development first:

- Local PostgreSQL in Docker
- Backend started from your terminal with `uvicorn`
- `STORAGE_BACKEND=local`

Only switch to AWS RDS or AWS S3 when you specifically need:

- the shared team database
- the shared S3 bucket
- production-like integration testing

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector, or Docker
- `psql`

### Terminal conventions

- macOS commands below assume `zsh` or `bash`
- Windows commands below assume PowerShell
- Docker commands are the same on both platforms unless noted otherwise

### 1. Create a virtual environment

#### macOS

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows PowerShell

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment variables

#### macOS

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in the required keys from the [Environment Variables](#environment-variables) section.

### 3. Start a local PostgreSQL with pgvector

```bash
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

### 4. Run database schema setup

#### macOS

```bash
psql -h localhost -U project20 -d project20_dev -f db/migrations/001_schema.sql
```

Optional dev seed data:

```bash
psql -h localhost -U project20 -d project20_dev -f db/migrations/999_seed_dev_data.sql
```

#### Windows PowerShell

```powershell
psql -h localhost -U project20 -d project20_dev -f db/migrations/001_schema.sql
```

Optional dev seed data:

```powershell
psql -h localhost -U project20 -d project20_dev -f db/migrations/999_seed_dev_data.sql
```

### 5. Start the API

#### macOS

```bash
uvicorn app.main:app --reload --port 8000
```

#### Windows PowerShell

```powershell
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- DB health check: [http://127.0.0.1:8000/health/db](http://127.0.0.1:8000/health/db)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google AI Studio key for embeddings |
| `OPENROUTER_API_KEY` | Yes | OpenRouter key for LLM completions |
| `JWT_SECRET_KEY` | Yes | Secret for signing JWTs |
| `GOOGLE_CLIENT_ID` | OAuth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth | Google OAuth client secret |
| `STORAGE_BACKEND` | No | `local` (default) or `s3` |
| `S3_BUCKET_NAME` | S3 | S3 bucket name for file uploads |
| `AWS_REGION` | S3 | AWS region, default `ap-southeast-2` |
| `AWS_PROFILE_NAME` | S3 | AWS profile name for SSO-based local access |
| `AWS_ACCESS_KEY_ID` | S3 | AWS credentials, if not using SSO/profile |
| `AWS_SECRET_ACCESS_KEY` | S3 | AWS credentials |
| `CORS_ORIGINS` | No | JSON array of allowed origins |
| `DEBUG` | No | `true` enables dev-token endpoint and relaxed CORS |
| `FRONTEND_URL` | No | SPA URL for OAuth redirect |

Generate a JWT secret:

#### macOS

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Windows PowerShell

```powershell
py -c "import secrets; print(secrets.token_hex(32))"
```

### Example local `.env`

```bash
DATABASE_URL=postgresql://project20:localdev123@localhost:5432/project20_dev
GEMINI_API_KEY=REMOVED_SECRET
OPENROUTER_API_KEY=REMOVED_SECRET
JWT_SECRET_KEY=replace-me
STORAGE_BACKEND=local
DEBUG=true
```

## AWS RDS Setup

Use this only if your backend should connect to the shared remote PostgreSQL database on AWS.

This section does not start your backend for you. It only changes where your backend stores and reads database data from.

### 1. Download the RDS SSL certificate

#### macOS

```bash
curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
```

#### Windows PowerShell

```powershell
Invoke-WebRequest -Uri "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem" -OutFile "global-bundle.pem"
```

### 2. Test the RDS connection

#### macOS

```bash
export RDSHOST="project20-db-pg16.cntu207sfdan.ap-southeast-2.rds.amazonaws.com"

psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem"
```

#### Windows PowerShell

```powershell
$env:RDSHOST = "project20-db-pg16.cntu207sfdan.ap-southeast-2.rds.amazonaws.com"

psql "host=$env:RDSHOST port=5432 dbname=postgres user=project20 sslmode=verify-full sslrootcert=./global-bundle.pem"
```

### 3. Run schema migration on RDS

#### macOS

```bash
psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem" \
  -f db/migrations/001_schema.sql

psql "host=$RDSHOST port=5432 dbname=postgres user=project20 \
  sslmode=verify-full sslrootcert=./global-bundle.pem" \
  -c "\dt"
```

#### Windows PowerShell

```powershell
psql "host=$env:RDSHOST port=5432 dbname=postgres user=project20 sslmode=verify-full sslrootcert=./global-bundle.pem" -f db/migrations/001_schema.sql

psql "host=$env:RDSHOST port=5432 dbname=postgres user=project20 sslmode=verify-full sslrootcert=./global-bundle.pem" -c "\dt"
```

Do not run `999_seed_dev_data.sql` on production.

### 4. Point the backend at RDS

```bash
DATABASE_URL=postgresql://project20:PASSWORD@project20-db-pg16.cntu207sfdan.ap-southeast-2.rds.amazonaws.com:5432/postgres?sslmode=verify-full&sslrootcert=./global-bundle.pem
STORAGE_BACKEND=s3
S3_BUCKET_NAME=team8-project20-materials
AWS_REGION=ap-southeast-2
```

## AWS S3 Setup with AWS SSO

Use this only if your backend should upload and read files from the shared AWS S3 bucket.

This section is independent from Docker. You can:

- run the backend locally and use local storage
- run the backend locally and use AWS S3
- run the backend in Docker and still use AWS S3

If you do not need the shared bucket, keep `STORAGE_BACKEND=local`.

### 1. Install AWS CLI

#### macOS

```bash
brew install awscli
aws --version
```

#### Windows PowerShell

```powershell
winget install Amazon.AWSCLI
aws --version
```

### 2. Configure AWS SSO

```text
aws configure sso
```

Use:

- SSO start URL: `https://uoa-sso.awsapps.com/start/#`
- SSO region: `ap-southeast-2`
- Profile name: for example `uoa-sso`

### 3. Log in before starting the backend

```text
aws sso login --profile uoa-sso
aws s3 ls --profile uoa-sso
```

If the bucket `team8-project20-materials` appears, the connection is working.

### 4. Add S3 settings to `.env`

```bash
STORAGE_BACKEND=s3
AWS_PROFILE_NAME=uoa-sso
AWS_REGION=ap-southeast-2
S3_BUCKET_NAME=team8-project20-materials
```

## API Overview

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

Interactive docs are available at `/docs`.

### Swagger authentication

1. Call `POST /api/v1/auth/dev-token` with `{"email": "you@test.com", "role": "instructor"}`
2. Copy the returned `access_token`
3. Click `Authorize` in Swagger UI and paste the token

## Running Tests

Tests require a separate PostgreSQL database with pgvector.

### Create a test database

#### macOS

```bash
createdb project20_test
```

#### Windows PowerShell

```powershell
createdb project20_test
```

### Run tests

#### macOS

```bash
TEST_DATABASE_URL="postgresql://project20:localdev123@localhost:5432/project20_test" \
  pytest tests/ -v
```

#### Windows PowerShell

```powershell
$env:TEST_DATABASE_URL = "postgresql://project20:localdev123@localhost:5432/project20_test"
pytest tests/ -v
```

### Run a single test file

#### macOS

```bash
TEST_DATABASE_URL="postgresql://project20:localdev123@localhost:5432/project20_test" \
  pytest tests/api/test_auth.py -v
```

#### Windows PowerShell

```powershell
$env:TEST_DATABASE_URL = "postgresql://project20:localdev123@localhost:5432/project20_test"
pytest tests/api/test_auth.py -v
```

Notes:

- Tests skip automatically if `TEST_DATABASE_URL` is not set
- AI calls to Gemini and OpenRouter are mocked in tests

## Data Storage Map

| Data | Storage |
|---|---|
| Uploaded files (PDF, PPTX, DOCX) | S3, or `local_uploads/` in dev |
| Users, courses, enrollments | `users`, `courses`, `course_enrollments` |
| Material metadata and processing state | `materials` |
| Text chunks and 768-dim vectors | `material_chunks` with pgvector |
| Rubrics, question pools, questions | `rubrics`, `question_pools`, `questions` |
| Assessment config | `assessment_configs` |
| Session state and transcript | `assessment_sessions`, `transcript_messages` |
| AI summary | `ai_summaries` |
| Instructor grade and feedback | `instructor_feedback` |

## Inspect Data with `psql`

#### macOS

```bash
psql "$DB_URL" -c "
SELECT 'users' AS t, COUNT(*) FROM users UNION ALL
SELECT 'courses', COUNT(*) FROM courses UNION ALL
SELECT 'materials', COUNT(*) FROM materials UNION ALL
SELECT 'material_chunks', COUNT(*) FROM material_chunks UNION ALL
SELECT 'assessment_sessions', COUNT(*) FROM assessment_sessions UNION ALL
SELECT 'transcript_messages', COUNT(*) FROM transcript_messages UNION ALL
SELECT 'ai_summaries', COUNT(*) FROM ai_summaries;
"
```

```bash
psql "$DB_URL" -c "
SELECT title, processing_status, total_chunks FROM materials;
"
```

#### Windows PowerShell

```powershell
psql "$env:DB_URL" -c "
SELECT 'users' AS t, COUNT(*) FROM users UNION ALL
SELECT 'courses', COUNT(*) FROM courses UNION ALL
SELECT 'materials', COUNT(*) FROM materials UNION ALL
SELECT 'material_chunks', COUNT(*) FROM material_chunks UNION ALL
SELECT 'assessment_sessions', COUNT(*) FROM assessment_sessions UNION ALL
SELECT 'transcript_messages', COUNT(*) FROM transcript_messages UNION ALL
SELECT 'ai_summaries', COUNT(*) FROM ai_summaries;
"
```

```powershell
psql "$env:DB_URL" -c "
SELECT title, processing_status, total_chunks FROM materials;
"
```

## Docker

Docker commands below are the same on macOS and Windows.

Docker is for local development infrastructure. In this project it is mainly used to run:

- a local PostgreSQL database container
- optionally the backend container as well

Docker does not mean you are using AWS. It is a separate local workflow.

### Build the backend image

```bash
docker build -t project20-api .
```

### Run with Docker Compose

```bash
docker compose up
```

The project root `docker-compose.yml` starts:

- a local `pgvector/pgvector:pg15` database container
- the backend API container with hot reload

Use Docker Compose when you want both services local and containerized.

Do not use Docker Compose if your goal is specifically:

- connecting your local backend directly to AWS RDS
- running against the shared AWS S3 bucket without containerizing the backend
