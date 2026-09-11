# WhereRU - Team 8 COMPSCI 399 Capstone Project

## Portfolio demo mode

The frontend includes an environment-controlled portfolio mode with fictional
course, assessment, student, transcript, rubric, and AI feedback data. It uses
the existing UI and intercepts requests at the frontend transport boundary, so
demo mode does not contact the configured API.

To enable it locally, create a local `.env` file (do not commit it) with:

```bash
VITE_DEMO_MODE=true
```

Then start the frontend:

```bash
npm install
npm run dev
```

Open these routes for the portfolio views (the demo instructor session is
provided automatically):

- `/instructor/demo-course-220/dashboard` — instructor dashboard
- `/instructor/demo-course-220/assessments/generate` — material upload, rubric, and AI question generation
- `/student/demo-course-220/demo-assessment-oral-1` — student oral assessment workflow
- `/instructor/transcript/demo-session-2` — instructor transcript and feedback review

To return to normal API-backed behaviour, set the local value to
`VITE_DEMO_MODE=false` (or remove it), restart Vite, and sign in normally.

The demo fixtures live under `src/mocks/` and contain no production records or
credentials.

## Name of the project

WhereRU

---

## Link to the Project Management tool

https://github.com/orgs/uoa-compsci399-s1-2026/projects/20

---

## Project Overview

This project is an AI-powered assessment system designed to support instructors in creating assessments and students in completing them within a controlled, timed environment. The system integrates large language models (LLMs) to create questions, evaluate answers and generate feedback.

### Key Features

- Upload course materials and generate a pool of questions which is editable by instructor
- Rubric table for instructors to define precise evaluation dimensions, ensuring grading consistency
- Short text-based chat assessment with adaptive follow-up questions
- Secure recording and storage of full conversation transcripts
- Instructor dashboard to review sessions and add manual judgement and feedback comments
- Automatic summary of each student’s demonstrated understanding (advisory only)
- Integrated with AWS Transcribe for Speech-to-Text feature with a user-confirmation loop to ensure transcript accuracy before evaluation

---

## Live Demo

https://where-areyou.com

### Login Requirements

- Gmail login credentials for a student account
- UoA email login credentials for an instructor account. If you do not have one, please feel free to contact me.

## Deployment

The application is deployed on an AWS EC2 instance and is accessible via a public URL for demonstration and evaluation purposes.

### Domain Configuration

The application is accessible via a custom domain:

- **Current Version**: v1.0.0
- **Domain**: where-areyou.com
- **DNS**: A record pointing to EC2 public IP
- **Hosting**: AWS EC2 instance

---

## Tech Stack

### Backend

Language - Python 3.13

#### Web framework

fastapi==0.115.0
uvicorn[standard]==0.30.0

#### Database

sqlalchemy==2.0.35
psycopg[binary]==3.2.10
alembic==1.13.2
pgvector==0.3.5

#### Data validation

pydantic==2.9.0
pydantic-settings==2.5.0

#### Auth

python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

#### AWS

boto3==1.43.6
amazon-transcribe==0.6.2

#### File processing

pandas==3.0.2
python-multipart==0.0.12
pdfplumber==0.11.4
python-docx==1.1.2
python-pptx==1.0.2

#### HTTP client

httpx==0.27.0

#### Environment

python-dotenv==1.0.1

#### Rate limiting

slowapi==0.1.9

#### Testing

pytest==8.3.0
pytest-asyncio==0.24.0
pytest-mock==3.14.0
httpx==0.27.0
moto[s3]==5.0.0

#### Production server

gunicorn==23.0.0

### Frontend

#### Core Frontend Frameworks

react 19.2.4
react-dom 19.2.4
react-router 7.13.1
vite 8.0.0
vitejs/plugin-react 6.0.0

#### API & State Management

tanstack/react-query 4.44.0
tanstack/react-query-devtools 4.44.0
axios 1.14.0

#### Authentication

react-oauth/google 0.13.4

#### UI Components & User Experience

react-datepicker 9.1.0
react-hot-toast 2.6.0
tailwind-datepicker-react 1.4.3
recharts 3.8.1

#### Styling & CSS Tools

tailwindcss 3.4.19
postcss 8.5.8
autoprefixer 10.4.27
prettier-plugin-tailwindcss 0.7.2

#### Formatting

eslint/js9.39.4
types/react 19.2.14
types/react-dom 19.2.3
eslint 9.39.4
eslint-plugin-react-hooks 7.0.1
eslint-plugin-react-refresh 0.5.2
globals 17.4.0
prettier 3.8.1

#### Testing

playwright/test 1.49.0

### Database

- PostgreSQL (via Amazon RDS)
- pgvector (extension for vector database)

### Cloud / Infrastructure

- Amazon RDS (PostgreSQL database)
- Amazon S3 (file storage)
- Amazon Bedrock (Claude 3 Haiku as primary LLM)
- Amazon Transcribe (Speech-to-Text feature)
- Amazon EC2 (Deployment and security group)
- Amazon IAM (Identity and Access Management)

### AI Integration

- AWS Bedrock – Claude 3 Haiku as Primary Model:
  - Generate questions
  - Answer evaluation
  - Feedback generation
  - Follow-up questions
- Embeddings support (e.g., Gemini)
- OpenRouter (Free Models) as Fallback Model:
  - Used as a backup when:
    - Primary model fails
    - API limits are reached
    - Network or service issues occur

---

## System Architecture

```text
Frontend (React)
       ↓
FastAPI Backend
       ↓
AWS RDS PostgreSQL
       ↓
AWS Bedrock / OpenRouter
```

---

## Project Structure

```plaintext
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes (router.py + routes/)
│   │   ├── core/             # config, database, security, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic (AI gateway, S3, RAG, etc.)
│   │   ├── utils/
│   │   ├── __init__.py
│   │   └── main.py           # Application entry point
│   │
│   ├── tests/                # Backend tests
│   ├── .env.example          # Environment variables template
│   ├── pytest.ini
│   ├── requirements.txt
│   └── README.md             # Deprecated — see root README.md
│
├── src/                      # Frontend source (Vite + React)
│   ├── features/             # Feature modules
│   │   ├── authentication/
│   │   ├── instructor/
│   │   └── student/
│   ├── hooks/                # Custom React hooks
│   ├── pages/                # Home, Login, PageNotFound
│   ├── services/             # API clients
│   ├── ui/                   # Reusable UI components
│   ├── utils/
│   ├── App.jsx
│   ├── main.jsx
│   └── Index.css
│
├── public/                   # Static assets
├── tests/                    # Playwright e2e + fixtures
│   ├── e2e/
│   └── fixtures/
├── docs/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── playwright.config.js
├── eslint.config.js
├── prettier.config.js
├── postcss.config.js
├── .env.example              # Frontend environment variables template
├── .gitignore
└── README.md

```

---

## Local Development Setup

This guide covers two paths:

- **Outside reviewers** — run everything locally (local database + AWS via IAM access keys)
- **Team members** — connect to the shared AWS RDS database and use UoA AWS SSO

The two paths differ at **Step 2 (database)**, **Step 3 (DATABASE_URL value)**, and **Step 5 (AWS access)**. All other steps are the same.

### Prerequisites

**Both paths need:**

- Python 3.13
- Node.js 18+

**Outside reviewers also need:**

- Docker (used to run PostgreSQL locally)

**Team members also need:**

- AWS CLI v2 (used to log in via UoA SSO)

### 1. Clone the repository

```bash
git clone https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-8.git
cd capstone-project-s1-2026-team-8
```

### 2. Set up the database — pick your path

#### For outside reviewers

Start a local PostgreSQL container with the pgvector extension:

**macOS / Linux**

```bash
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

**Windows PowerShell**

```powershell
docker run --name project20-db `
  -e POSTGRES_DB=project20_dev `
  -e POSTGRES_USER=project20 `
  -e POSTGRES_PASSWORD=localdev123 `
  -p 5432:5432 `
  -d pgvector/pgvector:pg16
```

Load the included `backend/schema.sql` into the container (same command on both platforms):

```bash
docker cp backend/schema.sql project20-db:/tmp/schema.sql
docker exec project20-db psql -U project20 -d project20_dev -f /tmp/schema.sql
```

#### For team members

Download the RDS SSL certificate into the `backend/` folder. The shared database requires SSL with `sslmode=verify-full`.

**macOS / Linux**

```bash
cd backend
curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
cd ..
```

**Windows PowerShell**

```powershell
cd backend
Invoke-WebRequest -Uri "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem" -OutFile "global-bundle.pem"
cd ..
```

### 3. Configure backend environment variables

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and fill in the `<...>` placeholders. Set `DATABASE_URL` based on your path:

Use a deployment-specific PostgreSQL 16 connection URL in the psycopg 3
SQLAlchemy format:

```
postgresql+psycopg://<user>:<password>@<host>:5432/<database>
```

For an RDS deployment, add the SSL parameters and CA path required by that
environment. Do not commit a real endpoint, username, password, or CA path.

Generate a value for `JWT_SECRET_KEY`:

```bash
python3.13 -c "import secrets; print(secrets.token_hex(32))"
```

```powershell
py -3.13 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Configure frontend environment variables

From the project root:

```bash
cd ..
cp .env.example .env
```

Fill in `VITE_GOOGLE_CLIENT_ID`.

### 5. Set up AWS credentials — pick your path

The backend needs AWS to call S3, Bedrock, and Transcribe.

#### For outside reviewers

Use the IAM access key pair.

In `backend/.env`:

1. Comment out the line `AWS_PROFILE_NAME=uoa-sso`
2. Uncomment and fill in:
   ```
   AWS_ACCESS_KEY_ID=<aws-access-key-id>
   AWS_SECRET_ACCESS_KEY=<aws-secret-access-key>
   ```

That's all. You do **not** need to install or configure the AWS CLI.

#### For team members

Install the AWS CLI v2:

**macOS**

```bash
brew install awscli
aws --version
```

**Windows PowerShell**

```powershell
winget install Amazon.AWSCLI
aws --version
```

**Linux** — follow the [official installer](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

Set up the AWS CLI to use UoA SSO:

```bash
aws configure sso
```

Use these values:

- SSO start URL: `https://uoa-sso.awsapps.com/start/#`
- SSO region: `ap-southeast-2`
- Profile name: `uoa-sso`

Then log in (re-run this every ~8 hours):

```bash
aws sso login --profile uoa-sso
```

Keep `AWS_PROFILE_NAME=uoa-sso` in `backend/.env` (this is the default in `.env.example`).

### 6. Start the backend

**macOS / Linux**

```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Windows PowerShell**

```powershell
cd backend
# Only needed once if you have never enabled PowerShell scripts:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 7. Start the frontend

Open a new terminal in the project root:

```bash
npm install
npm run dev
```

### 8. Open the app

- Frontend: http://localhost:5173
- Backend Swagger UI: http://127.0.0.1:8000/docs

---

## Assessment Workflow

```text
Instructor uploads materials and fill out rubric form
        ↓
AI generates question pool
        ↓
Instructor reviews and edits questions
        ↓
Assessment published
        ↓
Student completes timed session
        ↓
AI evaluates responses
        ↓
Instructor reviews and releases feedback
        ↓
Student reviews the results
```

---

## Usage Examples

### Instructor Workflow

Example workflow for instructors:

1. Login as instructor using Google Auth
2. Create a course
3. Enrol students and instructors to the course
4. Upload learning materials and fill out rubric table
5. Create an assessment
6. Review and edit AI-generated questions
7. Save the draft assessment
8. Release assessment to students
9. Detect potential cheating by anti-cheating system
10. Review AI-generated grading and feedback

### Student Workflow

Example workflow for students:

1. Login as student
2. View assessment requirement
3. Start assessment session
4. Answer AI-generated oral questions by recording audio
5. Adjust the transcribed text answer before submitting
6. Respond to adaptive follow-up questions
7. Submit assessment
8. View released feedback and results
9. Review previous assessment feedback and results

---

## Design Decisions

### Structured Output

AI responses are enforced in structured JSON format to:

- simplify frontend rendering
- improve response consistency
- reduce parsing errors

### LLM Fallback Strategy

- reliability under failure

### Layered Architecture

The backend follows a layered architecture:

- API layer
- service layer
- database layer

---

## Future Improvements

- Adaptive question difficulty
- Better anti-cheating mechanisms
- Improved prompt optimization
- Course management
- Timer for each question
- Real-time monitoring dashboard
- Role-Based Access Control for instructors
- Concurrency

---

## Authors & Contributors

COMPSCI 399 – Team 8 Next Level

- **Bess Zhang**
- **Joanne Chen**
- **Yihuan Tang**
- **Henry Song**
- **Whilin Zhao**
- **James Wilner**

## Acknowledgements

People consulted:

- **Shyamli Sindhwani**
- **Anna Trofimova**
- **Tony Feng**
