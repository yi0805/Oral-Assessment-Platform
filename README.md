# COMPSCI 399 Team 8 Capstone Project: WhereRU

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
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic

### Frontend
- React (Vite)
- JavaScript / JSX
- Tailwind CSS

### Cloud / Infrastructure
- AWS RDS (PostgreSQL)
- AWS S3 (optional for file storage)
- AWS Bedrock (Claude 3 Haiku as primary LLM)
- AWS Transcribe (STT)
- AWS EC2 (Deployment and security group)

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
git clone https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-8.git`
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

* **Bess Zhang**
* **Joanne Chen**
* **Yihuan Tang**
* **Henry Song**
* **Whilin Zhao**
* **James Wilner**
