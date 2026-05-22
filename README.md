# WhereRU - Team 8 COMPSCI 399 Capstone Project

## Name of the project

WhereRU

---

## Link to the Project Management tool

https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-8.git

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

http://where-areyou.com

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

Languague - Python 3.11+

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

Frontend (React)
↓
FastAPI Backend
↓
AWS RDS PostgreSQL
↓
AWS Bedrock / OpenRouter

---

## Project Structure

```plaintext
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Configurations and core logic
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── utils/        # Utility functions
│   │   ├── __init__.py
│   │   └── main.py       # Application entry point
│   │
│   ├── tests/            # Backend tests
│   ├── .env.example      # Environment variables template
│   ├── requirements.txt
│   ├── pytest.ini
│   └── README.md
│
├── frontend/
│   ├── public/           # Static assets
│   ├── src/
│   │   ├── features/     # Feature modules (auth, instructor, student)
│   │   ├── hooks/        # Custom React hooks
│   │   ├── pages/        # Page-level components
│   │   ├── services/     # API calls
│   │   ├── ui/           # Reusable UI components
│   │   ├── utils/        # Utility functions
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── .gitignore
└── README.md

```

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector, or Docker
- `psql`

1. Clone Repository

```bash
git clone https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-8.git
```

2. Configure environment variables

```bash
cp .env.example .env
```

3. Start PostgreSQL

```bash
docker run --name project20-db \
  -e POSTGRES_DB=project20_dev \
  -e POSTGRES_USER=project20 \
  -e POSTGRES_PASSWORD=localdev123 \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

4. Start Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

5. Frontend Setup:

```bash
cd src

npm install
npm run dev
```

6. Link

#### Frontend

http://localhost:5173

#### Backend Swagger UI

http://127.0.0.1:8000/docs

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
2. View assessment requirment
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
