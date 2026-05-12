# COMPSCI 399 Team 8 Capstone Project

## Project Overview

This project is an AI-powered assessment system designed to support instructors in creating assessments and students in completing them within a controlled, timed environment. The system integrates large language models (LLMs) to create questions, evaluate answers and generate feedback.


### Key Features
- Upload course materials and generate a small pool of questions (editable by instructor)
- Rubric table for instructors to define and edit marking criteria
- Short text-based chat assessment with adaptive follow-up questions
- Secure recording and storage of full conversation transcripts
- Instructor dashboard to review sessions and add manual judgement and feedback comments
- Automatic summary of each student’s demonstrated understanding (advisory only)
- Integrated with AWS Transcribe for accurate transcription of student answers

---

## Deployment

The application is deployed on an AWS EC2 instance and is accessible via a public URL for demonstration and evaluation purposes.

### Domain Configuration
The application is accessible via a custom domain:

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

## Local Run
1. `git clone https://github.com/uoa-compsci399-s1-2026/capstone-project-s1-2026-team-8.git`
2. Configure environment variables

#### macOS

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Edit `.env` and fill in the required keys from the [Environment Variables](#environment-variables) section.

3. Run `docker-compose up --build`

4. Backend Setup:

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
5. Run backend:
```bash
uvicorn app.main:app --reload --port 8000
```

6. Frontend Setup
```bash
npm install
npm run dev
```

---

## Authors & Contributors

COMPSCI 399 – Team 8 Next Level

* **Bess Zhang**
* **Joanne Chen**
* **Yihuan Tang**
* **Henry Song**
* **Whilin Zhao**
* **James Wilner**
