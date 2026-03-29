# Project 20 Backend API

Backend service for the AI-Supported Oral Assessment Tool.

## Current design alignment

This repository is structured around the Project 20 end-to-end flow:

- instructor uploads course materials and a rubric
- AI generates or supports question creation
- instructor publishes an assessment
- student completes a timed chat-based assessment
- transcript is stored securely
- AI generates an advisory summary
- instructor makes the final judgement and releases results
- student can view released feedback and the transcript

See `docs/end_to_end_user_flow.md` for the detailed workflow assumptions.

## Quick start

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Prepare environment variables
cp .env.example .env

# 4. Start PostgreSQL locally in Docker
# This command can be run from any folder.
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16

# 5. Run migrations from the project root
psql -h localhost -U project20 -d project20_dev -f db/migrations/001_schema.sql

psql -h localhost -U project20 -d project20_dev -f db/migrations/999_seed_dev_data.sql

# 6. Start the API server
uvicorn app.main:app --reload --port 8000
```

## Data model notes

- `assessment_mode` controls where main questions come from.
- `question_pool_id` is required for `generic` assessments and optional for `personalized` assessments.
- The backend no longer enforces a hard `max_main_questions` column.
- `max_followups_per_main` is still configurable because adaptive follow-ups are part of the runtime rules.
- `released_to_student` and `released_at` control when student-visible results become available.


## Troubleshooting

If you already ran an older broken migration set, recreate the local database before rerunning the SQL files.

```bash
docker rm -f project20-db
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16

psql -h localhost -U project20 -d project20_dev -f db/migrations/001_schema.sql

psql -h localhost -U project20 -d project20_dev -f db/migrations/999_seed_dev_data.sql
```

FastAPI docs are available at `http://127.0.0.1:8000/docs`.

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- AWS RDS database for PostgreSQL 16 with pgvector
- AWS S3 for file storage
- Google OAuth for authentication

