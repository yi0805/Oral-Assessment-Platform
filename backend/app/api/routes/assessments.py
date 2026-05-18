import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_instructor
from app.services import s3_client

from app.models import (
    AssessmentConfig, AssessmentSession, CourseEnrollment, User,
    Question, QuestionPool, Rubric, Material, MaterialChunk,
)
from app.schemas import (
    ReleaseResponse,
    AssessmentConfigDetailOut,
    AssessmentConfigUpdate,
    AssessmentConfigSummary,
    AssessmentCopyRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Release assessment

@router.post(
    "/courses/{course_id}/assessments/{assessment_config_id}/release",
    response_model=ReleaseResponse,
    summary="Release an assessment to students",
)
def release_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    # Verify instructor enrollment 
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    # Validate assessment config
    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if config.status != "draft":
        raise HTTPException(status_code=409, detail="Assessment is already published or closed.")

    duplicate_title = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.course_id == course_id,
            AssessmentConfig.title == config.title,
            AssessmentConfig.status == "published",
        )
        .first()
    )

    if duplicate_title:
        raise HTTPException(
            status_code=409,
            detail=f"A published assessment titled '{config.title}' already exists in this course.",
        )

    if config.main_question_num is None:
        raise HTTPException(status_code=422, detail="main_question_num must be set before publishing.")

    # Validate question pool
    question_pool = (
        db.query(QuestionPool)
        .filter(QuestionPool.assessment_config_id == config.id)
        .first()
    )

    if not question_pool:
        raise HTTPException(status_code=422, detail="No question pool found for this assessment.")
    
    if question_pool.status != "draft":
        raise HTTPException(status_code=422, detail="Question pool was already published.")

    # Publish config and question pool
    question_pool.status = "published"

    # default release and due time if not stated
    now = datetime.now(timezone.utc)
    if not config.release_time:
        config.release_time = now
    if not config.due_time:
        config.due_time = now + timedelta(days=30)
    config.status = "published"

    # Create sessions for all enrolled students
    student_enrollments = (
        db.query(CourseEnrollment)
        .join(User, CourseEnrollment.user_id == User.id)
        .filter(
            CourseEnrollment.course_id == course_id,
            User.role == "student",
        )
        .all()
    )

    sessions_created = 0

    for enr in student_enrollments:
        db.add(AssessmentSession(
            assessment_config_id=config.id,
            user_s_id=enr.user_id,
            status="not_started",
        ))
        sessions_created += 1

    try:
        db.commit()
        
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to release assessment due to a server error.")

    return ReleaseResponse(sessions_created=sessions_created)


# List assessment configs for a course

@router.get(
    "/courses/{course_id}/assessments",
    response_model=list[AssessmentConfigSummary],
    summary="List all assessment configs for a course (instructor view)",
)
def list_course_assessments(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    configs = (
        db.query(AssessmentConfig)
        .filter(AssessmentConfig.course_id == course_id)
        .order_by(AssessmentConfig.title.asc())
        .all()
    )

    return configs


# Get assessment config

@router.get(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    response_model=AssessmentConfigDetailOut,
    summary="Get assessment config details",
)
def get_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    return config


# Update assessment config

@router.put(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    response_model=AssessmentConfigDetailOut,
    summary="Update an assessment config",
)
def update_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    payload: AssessmentConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    update_data = payload.model_dump(exclude_unset=True)

    if config.status != "draft":
        disallowed = set(update_data.keys()) - {"due_time", "title"}
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only the due date and the title can be updated for a published assessment.",
            )

    if "main_question_num" in update_data and update_data["main_question_num"] is not None:
        pool_size = 0
        if config.question_pool:
            pool_size = (
                db.query(Question)
                .filter(Question.question_pool_id == config.question_pool.id)
                .count()
            )

        if update_data["main_question_num"] > pool_size:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"main_question_num ({update_data['main_question_num']}) "
                    f"cannot exceed the question pool size ({pool_size}). "
                    f"Add more questions first."
                ),
            )

    for field, value in update_data.items():
        setattr(config, field, value)

    try:
        db.commit()
        db.refresh(config)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")

    return config


# Delete assessment config

@router.delete(
    "/courses/{course_id}/assessments/{assessment_config_id}",
    summary="Delete an assessment config",
)
def delete_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for this course.")

    config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if config.status == "published":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a published assessment.")

    try:
        db.delete(config)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database deletion failed")

    return {"message": "Assessment deleted successfully."}


# Copy assessment

@router.post(
    "/courses/{course_id}/assessments/{assessment_config_id}/copy",
    response_model=AssessmentConfigSummary,
    summary="Copy an assessment to the same or a different course",
)
def copy_assessment(
    course_id: UUID,
    assessment_config_id: UUID,
    payload: AssessmentCopyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor),
):
    # Verify instructor is enrolled in the source course
    source_enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not source_enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for the source course.")

    # Verify instructor is enrolled in the target course
    target_enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == payload.target_course_id,
            CourseEnrollment.user_id == current_user.id,
        )
        .first()
    )
    if not target_enrollment:
        raise HTTPException(status_code=403, detail="You are not an instructor for the target course.")

    # Load source assessment
    source_config = (
        db.query(AssessmentConfig)
        .filter(
            AssessmentConfig.id == assessment_config_id,
            AssessmentConfig.course_id == course_id,
        )
        .first()
    )
    if not source_config:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    source_rubric = db.query(Rubric).filter(Rubric.id == source_config.rubric_id).first()
    if not source_rubric:
        raise HTTPException(status_code=404, detail="Source rubric not found.")

    source_pool = (
        db.query(QuestionPool)
        .filter(QuestionPool.assessment_config_id == source_config.id)
        .first()
    )
    if not source_pool:
        raise HTTPException(status_code=422, detail="Source assessment has no question pool to copy.")

    new_title = payload.title if payload.title else f"Copy of {source_config.title}"

    is_cross_course = payload.target_course_id != course_id

    source_materials = list(source_pool.materials)

    if not source_materials:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source assessment has no materials to copy.",
        )

    new_storage_keys: list[str] = []

    new_material_specs: list[dict] = []

    if is_cross_course:
        for src_mat in source_materials:
            new_mid = uuid4()
            new_key = s3_client.generate_key(
                payload.target_course_id, new_mid, src_mat.filename
            )

            try:
                s3_client.copy_object(src_mat.storage_key, new_key)

            except RuntimeError as exc:
                for k in new_storage_keys:
                    try:
                        s3_client.delete_file(k)

                    except Exception:
                        logger.exception(
                            "Cleanup failed during copy_assessment S3 rollback: key=%s",
                            k,
                        )

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Storage copy failed: {exc}",
                ) from exc

            new_storage_keys.append(new_key)
            new_material_specs.append({
                "new_id": new_mid,
                "new_storage_key": new_key,
                "source": src_mat,
            })

    # Orphan cleanup: if S3 copies succeeded but DB writes fail, drop the new objects
    def _cleanup_orphan_storage() -> None:
        for key in new_storage_keys:
            try:
                s3_client.delete_file(key)

            except Exception:
                logger.exception(
                    "Orphan S3 object after copy_assessment rollback; "
                    "manual cleanup needed: storage_key=%s",
                    key,
                )

    try:
        new_materials: list[Material] = []

        if is_cross_course:
            for spec in new_material_specs:
                src = spec["source"]
                new_material = Material(
                    id=spec["new_id"],
                    course_id=payload.target_course_id,
                    filename=src.filename,
                    mime_type=src.mime_type,
                    storage_key=spec["new_storage_key"],
                    material_category=src.material_category,
                )
                
                db.add(new_material)
                new_materials.append(new_material)

                source_chunks = (
                    db.query(MaterialChunk)
                    .filter(MaterialChunk.material_id == src.id)
                    .order_by(MaterialChunk.chunk_index)
                    .all()
                )

                db.add_all([
                    MaterialChunk(
                        material_id=spec["new_id"],
                        chunk_index=ch.chunk_index,
                        chunk_text=ch.chunk_text,
                        embedding=ch.embedding,
                    )
                    for ch in source_chunks
                ])

        # Copy rubric (independent from original)
        new_rubric = Rubric(
            course_id=payload.target_course_id,
            total_points=source_rubric.total_points,
            criteria_data=source_rubric.criteria_data,
        )
        db.add(new_rubric)
        db.flush()

        # Copy assessment config (reset status and dates)
        new_config = AssessmentConfig(
            course_id=payload.target_course_id,
            title=new_title,
            description=source_config.description,
            rubric_id=new_rubric.id,
            total_time_minute=source_config.total_time_minute,
            main_question_num=source_config.main_question_num,
            follow_up_num=source_config.follow_up_num,
            release_time=None,
            due_time=None,
            status="draft",
        )
        db.add(new_config)
        db.flush()

        # Copy question pool and its questions
        new_pool = QuestionPool(
            assessment_config_id=new_config.id,
            status="draft",
        )
        db.add(new_pool)
        db.flush()


        new_pool.materials = new_materials if is_cross_course else source_materials

        source_questions = (
            db.query(Question)
            .filter(Question.question_pool_id == source_pool.id)
            .order_by(Question.question_index)
            .all()
        )
        db.add_all([
            Question(
                question_pool_id=new_pool.id,
                question_text=q.question_text,
                question_index=q.question_index,
            )
            for q in source_questions
        ])

        db.commit()
        db.refresh(new_config)

    except IntegrityError as exc:
        db.rollback()
        logger.warning("copy_assessment integrity violation", exc_info=True)
        _cleanup_orphan_storage()
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Copy violates a database constraint.",
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("copy_assessment failed")
        _cleanup_orphan_storage()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to copy assessment.",
        ) from exc

    return new_config