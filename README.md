# WhereRU — AI-Powered Oral Assessment Platform

WhereRU is a full-stack AI assessment platform for creating and running adaptive oral assessments from course materials. Instructors can generate and edit question pools, define rubrics, review student sessions, and release feedback; students complete timed oral assessments with transcript confirmation and AI-assisted follow-up questions.

**Live demo:** https://where-areyou.com  
**University of Auckland:** COMPSCI 399 Capstone Project — Team 8  
**Core stack:** React · FastAPI · PostgreSQL · pgvector · AWS · WebSockets · LLM/RAG

> The original capstone implementation includes AWS Transcribe streaming and Bedrock/OpenRouter-based AI paths. The current public demo is deployed with a lower-cost production configuration; see [Current Demo Deployment](#current-demo-deployment) for the exact runtime.

---

## Why this project is interesting

WhereRU goes beyond a basic LLM wrapper. It combines a real assessment workflow with document ingestion, retrieval, structured AI output, live speech processing, instructor review, authentication, persistence, production deployment, and automated tests.

### Engineering highlights

- **Adaptive oral assessment workflow** — generates questions from course materials and supports follow-up questions based on student responses.
- **RAG-backed course context** — stores and retrieves material embeddings with PostgreSQL + pgvector.
- **Real-time speech-to-text work** — implements AWS Transcribe Streaming over WebSockets with a batch fallback path.
- **Measured performance optimisation** — reduced median time-to-first-text from **18.21 s** in the original batch baseline to **~1.85 s** for the streaming path.
- **Production deployment** — React and FastAPI deployed behind Nginx on AWS EC2 with RDS PostgreSQL and S3 storage.
- **Engineering safeguards** — rate limiting, authentication, prompt-safety handling, recovery paths, backend tests, and Playwright end-to-end coverage.

---

## Performance highlight: speech-to-text latency

The original assessment flow used batch transcription, which could leave the UI waiting for many seconds before any transcript appeared. The streaming implementation returns partial text while the student is still speaking.

| Path | Median / typical result | User-visible behaviour |
| --- | ---: | --- |
| Original batch baseline | **18.21 s** median total | Transcript appears after processing completes |
| Batch after polling improvement | **7.79 s** median total | Faster completion, but still batch-oriented |
| Streaming | **~1.85 s** median time-to-first-partial | Text begins appearing close to real time |

That is roughly an **89.8% reduction in time to first visible text** compared with the original batch baseline.

The repository includes the measurement methodology, raw timing model, caveats, and benchmark design in [`docs/stt-baseline.md`](docs/stt-baseline.md).

---

## My contributions

This was a six-person capstone project. The following are selected contributions I worked on and later strengthened in this portfolio repository:

- Optimised and benchmarked the speech-to-text pipeline, including streaming behaviour, timing instrumentation, and fallback handling.
- Added a reproducible STT benchmark harness and documented matched measurements instead of relying on subjective performance claims.
- Hardened WebSocket/audio-stream lifecycle behaviour and authentication-related helpers around the streaming path.
- Added and refined AWS deployment configuration, Nginx/systemd production setup, environment safeguards, and deployment documentation.
- Improved production-readiness checks around material processing and application configuration.

For the STT optimisation details, see [`docs/stt-baseline.md`](docs/stt-baseline.md). For deployment details, see [`deployment/README.md`](deployment/README.md).

---

## Product workflow

```text
Instructor uploads course materials and defines a rubric
        ↓
System processes materials and builds retrieval context
        ↓
AI generates an editable question pool
        ↓
Instructor publishes the assessment
        ↓
Student completes a timed oral assessment
        ↓
Speech is transcribed and confirmed by the student
        ↓
AI evaluates responses and generates follow-up questions / feedback
        ↓
Instructor reviews the session and releases feedback
```

### Instructor features

- Create courses and manage enrolments
- Upload learning materials
- Define rubric criteria
- Generate and edit AI-assisted question pools
- Publish assessments
- Review transcripts, AI evaluation, and session history
- Add manual judgement and feedback before release

### Student features

- Sign in with Google authentication
- View available assessments
- Complete timed oral responses
- Confirm or correct transcribed text before evaluation
- Respond to adaptive follow-up questions
- Review released feedback and previous results

---

## Architecture

```mermaid
flowchart TD
    A[Browser] -->|HTTPS| B[Nginx on AWS EC2]
    B --> C[React / Vite Frontend]
    B --> D[FastAPI Backend]
    D --> E[(PostgreSQL / Amazon RDS)]
    E --> F[pgvector]
    D --> G[Amazon S3]
    D --> H[LLM Gateway]
    H --> I[OpenRouter / Gemini]
    H -. capstone path .-> J[AWS Bedrock]
    D -. optional STT path .-> K[AWS Transcribe Streaming]
```

The backend uses a layered structure with API routes, services, database models, Pydantic schemas, and infrastructure integrations separated by responsibility.

---

## Tech stack

### Frontend

- React 19
- React Router
- TanStack React Query
- Axios
- Tailwind CSS
- Recharts
- Google OAuth
- Playwright

### Backend

- Python 3.13
- FastAPI + Uvicorn / Gunicorn
- SQLAlchemy 2
- Pydantic
- PostgreSQL
- pgvector
- JWT-based application authentication
- SlowAPI rate limiting
- pytest

### AI / data

- Retrieval-augmented generation over uploaded course materials
- PostgreSQL + pgvector for vector search
- Structured JSON output for AI responses
- OpenRouter / Gemini integration
- AWS Bedrock integration retained from the capstone implementation

### Cloud / infrastructure

- AWS EC2
- Amazon RDS PostgreSQL
- Amazon S3
- AWS IAM
- Nginx
- systemd
- TLS via Let's Encrypt / Certbot
- AWS Transcribe Streaming implementation retained in the repository

---

## Current demo deployment

The public demo at https://where-areyou.com runs on AWS EC2 behind Nginx with a FastAPI backend, RDS PostgreSQL, and S3 storage.

The production runbook intentionally documents the exact current runtime separately from the broader capstone feature set. In the current low-cost demo configuration:

- chat requests use OpenRouter with a Gemini model
- embeddings use Gemini
- AWS Transcribe is disabled in the public production configuration
- the Transcribe streaming implementation, tests, and benchmark evidence remain in the repository

This separation keeps the demo inexpensive while preserving the engineering work and reproducible measurements from the original speech-to-text implementation.

See [`deployment/README.md`](deployment/README.md) for the production layout and safeguards.

---

## Testing

### Backend

The backend test suite covers areas including:

- audio streaming behaviour
- transcription flows
- material-processing recovery
- production safeguards
- response validation

Run:

```bash
cd backend
pytest
```

### End-to-end

Playwright coverage includes the streaming assessment flow.

```bash
npm run test:e2e
```

Frontend quality checks:

```bash
npm run lint
npm run build
```

---

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # configuration, database, auth, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # AI, RAG, S3 and application services
│   │   └── utils/            # shared utilities, including audio/STT helpers
│   └── tests/                # backend test suite
├── deployment/               # Nginx, systemd and production runbook
├── docs/                     # engineering notes and benchmarks
├── src/                      # React frontend
├── tests/e2e/                # Playwright tests
├── package.json
└── README.md
```

---

## Local development

### Prerequisites

- Python 3.13
- Node.js 18+
- Docker for a local PostgreSQL + pgvector database

### 1. Clone

```bash
git clone https://github.com/yi0805/Oral-Assessment-Platform.git
cd Oral-Assessment-Platform
```

### 2. Start PostgreSQL + pgvector

```bash
docker run --name whereru-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

Load the repository schema:

```bash
docker cp backend/schema.sql whereru-db:/tmp/schema.sql
docker exec whereru-db psql -U project20 -d project20_dev -f /tmp/schema.sql
```

### 3. Configure the backend

```bash
cd backend
cp .env.example .env
```

Use a local SQLAlchemy connection URL such as:

```text
postgresql+psycopg://project20:localdev123@localhost:5432/project20_dev
```

Generate a JWT secret:

```bash
python3.13 -c "import secrets; print(secrets.token_hex(32))"
```

Fill the remaining provider settings you intend to use in `backend/.env`. Do not commit credentials.

### 4. Configure the frontend

From the project root:

```bash
cp .env.example .env
```

Set the required frontend environment variables such as the Google OAuth client ID.

### 5. Start the backend

```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell, activate with:

```powershell
.\venv\Scripts\Activate.ps1
```

### 6. Start the frontend

```bash
npm install
npm run dev
```

Then open:

- Frontend: http://localhost:5173
- FastAPI docs: http://127.0.0.1:8000/docs

For the full AWS production procedure, use [`deployment/README.md`](deployment/README.md).

---

## Design decisions

### Structured AI output

AI responses are constrained to structured output so the application can validate results, render them consistently, and reduce brittle free-text parsing.

### Retrieval instead of prompt stuffing

Uploaded materials are processed into retrievable chunks rather than sending all source content with every request. This keeps the assessment flow more scalable and makes course context easier to control.

### Human-in-the-loop assessment

AI-generated grading and summaries are advisory. Instructors can review session evidence and add manual judgement before feedback is released.

### Streaming with recovery paths

The speech-to-text work was designed around user-visible latency, not only final transcription time. The streaming path therefore exposes partial results early while retaining recovery/fallback behaviour when streaming fails.

---

## Further improvements

Potential next steps include:

- adaptive question difficulty
- stronger role-based access control
- broader automated test coverage
- CI/CD automation
- infrastructure as code
- production monitoring and observability
- additional AI evaluation / regression datasets

---

## Authors and contributors

**COMPSCI 399 — Team 8 Next Level**

- Bess Zhang
- Joanne Chen
- Yihuan Tang
- Henry Song
- Whilin Zhao
- James Wilner

### Acknowledgements

People consulted during the capstone project:

- Shyamli Sindhwani
- Anna Trofimova
- Tony Feng
