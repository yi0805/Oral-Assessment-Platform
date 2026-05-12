from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor

from app.models import (
    AssessmentSession,
    SessionFeedback,
    User,
    AISummary,
    AssessmentConfig,
    CourseEnrollment,
)
from app.schemas import ReleaseAllReviews, GradeUpdate, InstructorReviewUpdate, AISummaryInfoOut, ApproveAllAiReviews

router = APIRouter()


# Helpers

def _get_session_or_404(
    db: Session,
    session_id: UUID,
    student_id: UUID,
    instructor_id: UUID,
) -> AssessmentSession:
    sess = (
        db.query(AssessmentSession)
        .join(
            AssessmentConfig,
            AssessmentSession.assessment_config_id == AssessmentConfig.id,
        )
        .join(
            CourseEnrollment,
            AssessmentConfig.course_id == CourseEnrollment.course_id,
        )
        .filter(
            AssessmentSession.id == session_id,
            AssessmentSession.user_s_id == student_id,
            CourseEnrollment.user_id == instructor_id,
        )
        .first()
    )

    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return sess


def _release_one_result(db: Session, session_id: UUID, student_id: UUID, instructor_id: UUID):
    sess = _get_session_or_404(db, session_id, student_id, instructor_id)

    if sess.status != "under_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This session's results have already been {sess.status}. "
                "No further action is needed."
            ),
        )

    feedback = (
        db.query(SessionFeedback)
        .filter(SessionFeedback.session_id == session_id)
        .first()
    )

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feedback found. Submit instructor feedback before releasing.",
        )

    if feedback.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This feedback has already been {feedback.status} "
                "and cannot be published again."
            ),
        )

    if feedback.final_grade is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="final_grade must be set before releasing results to the student.",
        )

    feedback.status = "published"
    sess.status = "released"

def join_detailed_feedback(summary):
    summary_text = " | ".join([
        f"{title}: {content['feedback']}" 
        for title, content in summary.detailed_feedback.items()
    ])
    return summary_text

# Release one result

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
    _release_one_result(db, session_id, student_id, current_user.id)
    db.commit()

    return {"message": f"Results released to student."}


# Release all results

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
            instructor_id=current_user.id,
        )

    db.commit()

    return {"message": "All results released successfully"}


@router.put(
    "/sessions/{session_id}/{student_id}/unpublish/session",
    summary="Unpublish one result"
)
def unpublish_result(
    session_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    sess = _get_session_or_404(db, session_id, student_id, current_user.id)

    if sess.status != "released":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This session's results is still {sess.status}. "
            ),
        )

    feedback = (
        db.query(SessionFeedback)
        .filter(SessionFeedback.session_id == session_id)
        .first()
    )

    if not feedback:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Feedback not found.",
    )

    if feedback.status != "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This feedback is still {feedback.status} "
            ),
        )

    feedback.status = "draft"
    sess.status = "under_review"

    db.commit()

    return {"message": f"Result unpublished successfully."}


# Update grade

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
        .join(
            AssessmentConfig,
            AssessmentSession.assessment_config_id == AssessmentConfig.id,
        )
        .join(
            CourseEnrollment,
            AssessmentConfig.course_id == CourseEnrollment.course_id,
        )
        .filter(
            AssessmentSession.id == session_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    feedback = (
        db.query(SessionFeedback)
        .filter(SessionFeedback.session_id == session_id)
        .first()
    )

    if feedback:
        if feedback.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot update grade: feedback has already been {feedback.status}. "
                    "Unpublish the result first to edit the grade."
                ),
            )
        
        feedback.final_grade = payload.grade
    else:
        feedback = SessionFeedback(
            session_id=session_id,
            user_i_id=current_user.id,
            final_grade=payload.grade,
            status="draft",
        )
        db.add(feedback)

    db.commit()
    db.refresh(feedback)

    return {"message": f"Grade updated successfully."}


# Upsert instructor review

@router.put("/sessions/{session_id}/review")
def upsert_review(
    session_id: UUID,
    payload: InstructorReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    session = (
        db.query(AssessmentSession)
        .join(
            AssessmentConfig,
            AssessmentSession.assessment_config_id == AssessmentConfig.id,
        )
        .join(
            CourseEnrollment,
            AssessmentConfig.course_id == CourseEnrollment.course_id,
        )
        .filter(
            AssessmentSession.id == session_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

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

    feedback.status = "published"
    session.status = "released"

    db.commit()
    db.refresh(feedback)
    db.refresh(session)

    return {"message": f"Instructor review saved for session."}


# Approve AI score helpers

def _approve_one_ai_grade(db: Session, session_id: UUID, instructor_id: UUID):
    sess = (
        db.query(AssessmentSession)
        .join(
            AssessmentConfig,
            AssessmentSession.assessment_config_id == AssessmentConfig.id,
        )
        .join(
            CourseEnrollment,
            AssessmentConfig.course_id == CourseEnrollment.course_id,
        )
        .filter(
            AssessmentSession.id == session_id,
            CourseEnrollment.user_id == instructor_id,
        )
        .first()
    )

    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    if sess.status != "under_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot accept AI grade for session with status '{sess.status}'. "
                "Session must be in 'under_review' state."
            ),
        )

    ai_summary = (
        db.query(AISummary)
        .filter(AISummary.session_id == session_id)
        .first()
    )

    comments = join_detailed_feedback(ai_summary)

    if not ai_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI summary found for this session.",
        )

    if ai_summary.suggested_grade is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AI summary did not produce a valid suggested grade.",
        )

    existing = (
        db.query(SessionFeedback)
        .filter(SessionFeedback.session_id == session_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already exists for this session.",
        )

    feedback = SessionFeedback(
        session_id=session_id,
        user_i_id=instructor_id,
        final_grade=ai_summary.suggested_grade,
        comments=comments,
        status="draft",
    )
    db.add(feedback)


# Approve single AI score

@router.post(
    "/sessions/{session_id}/ai-summary/approve",
    summary="Approve AI grade for a single session",
)
def accept_ai_and_release(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    _approve_one_ai_grade(db, session_id, current_user.id)
    db.commit()

    return {"message": "AI grade approved successfully."}


# Approve all AI scores

@router.post(
    "/sessions/ai-summary/approve/all",
    summary="Batch approve AI grades",
)
def approve_all_ai_grades(
    payload: ApproveAllAiReviews,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    if not payload.assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sessions provided.",
        )

    approved = 0
    skipped = 0

    for assessment in payload.assessments:
        try:
            _approve_one_ai_grade(db, assessment.session_id, current_user.id)
            approved += 1

        except HTTPException as exc:
            if (
                exc.status_code == status.HTTP_409_CONFLICT
                and "Feedback already exists" in (exc.detail if exc.detail else "")
            ):
                skipped += 1
                continue
            raise

    db.commit()

    return {
        "message": (
            f"Approved {approved}; skipped {skipped} (already graded)."
            if skipped
            else "All AI grades approved successfully."
        )
    }