"""Project 20 backend API entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


app = FastAPI(
    title="Project 20 API",
    description=(
        "Backend API for the AI-Supported Individualized Oral Assessment Tool."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# from app.api.router import api_router
# app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    """Basic API health check."""
    return {"status": "ok", "project": "Project 20", "version": "0.1.0"}


@app.get("/health/db", tags=["Health"])
def health_db():
    """Database connectivity check."""
    from sqlalchemy import text

    from app.core.database import engine

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            table_count = result.scalar()
        return {"status": "ok", "database": "connected", "tables": table_count}
    except Exception as exc:
        return {"status": "error", "database": str(exc)}
