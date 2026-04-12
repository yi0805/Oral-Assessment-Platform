from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.models import AssessmentSession, SessionFeedback, User
from app.schemas  import ReleaseAllReviews, GradeUpdate, InstructorReviewUpdate

router = APIRouter()

def _get_session_or_404(db: Session, session_id: UUID, student_id: UUID) -> AssessmentSession:
    q = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_s_id == student_id,
    )

    sess = q.first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    return sess

def _release_one_result(
    db: Session,
    session_id: UUID,
    student_id: UUID,
):
    sess = _get_session_or_404(db, session_id, student_id)

    feedback = db.query(SessionFeedback).filter(
        SessionFeedback.session_id == session_id
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback found. Submit instructor feedback before releasing.",
        )

    if feedback.final_grade is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="final_grade must be set before releasing results to the student.",
        )

    feedback.status = "published"

    sess.status = "released"


@router.put(
    "/sessions/{session_id}/{student_id}/release/session",
    summary="release one result",
)
def release_result(
    session_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _release_one_result(db, session_id, student_id)

    db.commit()
    
    return {"message": f"Results released to student {student_id} for session {session_id}."}


@router.put(
    "/sessions/release/allSessions",
    summary="Release all results",
)
def release_all_results(
    payload: ReleaseAllReviews,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    if not payload.assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sessions provided.",
        )

    for assessment in payload.assessments:
        _release_one_result(
            db=db,
            session_id=assessment.session_id,
            student_id=assessment.student_id,
        )

    db.commit()
    return {
        "message": "All results released successfully"
    }


@router.put(
    "/sessions/{session_id}/grade",
    summary="Integration",
)
def update_grade(
    session_id: UUID,
    payload: GradeUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    session = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.id == session_id)
        .first()
        )
   
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

   
    feedback = SessionFeedback(
        session_id=session_id,
        user_i_id=current_user.id,
        final_grade=payload.grade,
        status="draft",
    )

    db.add(feedback)

    db.commit()
    db.refresh(feedback)

    return {"message": f"Grade updated for session {session_id}."}

@router.put("/sessions/{session_id}/review")
def upsert_review(
    session_id: UUID,
    payload: InstructorReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    feedback = (
        db.query(SessionFeedback)
        .filter(SessionFeedback.session_id == session_id)
        .first()
    )


    if not feedback:
        feedback = SessionFeedback(
            session_id=session_id,
            user_i_id=current_user.id,
            final_grade=payload.final_grade,
            comments=payload.comments,
            status="draft",
        )
        db.add(feedback)
    else:
        feedback.final_grade = payload.final_grade
        feedback.comments = payload.comments

    session = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.id == session_id)
        .first()
    )

    feedback.status = "published"

    session.status = "released"

    db.commit()
    db.refresh(feedback)
    db.refresh(session)

    return {"message": f"Instructor review saved for session {session_id}."}