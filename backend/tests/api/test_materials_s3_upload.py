"""Integration test: instructor uploads a file to S3 (mocked via moto)."""
from __future__ import annotations

import boto3

from app.core.config import settings


def test_instructor_upload_pdf_to_s3(
    client_no_pipeline,
    instructor_course_setup,
    mock_s3_bucket,
    db_session,
):
    """
    POST /courses/{id}/materials/upload stores the object in S3 and returns 201.

    Uses moto for S3 and a real PostgreSQL row for auth/enrollment/material.
    """
    course_id = instructor_course_setup["course"].id
    headers = instructor_course_setup["headers"]

    pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    files = {"file": ("lecture.pdf", pdf_bytes, "application/pdf")}
    data = {"title": "Week 1 slides"}

    response = client_no_pipeline.post(
        f"/api/v1/courses/{course_id}/materials/upload",
        headers=headers,
        files=files,
        data=data,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "Week 1 slides"
    assert body["original_filename"] == "lecture.pdf"
    assert body["file_type"] == "pdf"
    assert body["processing_status"] == "uploaded"
    storage_key = body["storage_key"]
    assert storage_key.startswith(f"courses/{course_id}/materials/")
    assert storage_key.endswith("/lecture.pdf")

    s3 = boto3.client("s3", region_name=settings.aws_region)
    obj = s3.get_object(Bucket=mock_s3_bucket, Key=storage_key)
    assert obj["Body"].read() == pdf_bytes

    # cleanup material row (course/user cleaned by instructor_course_setup)
    from app.models.material import Material

    mid = body["id"]
    db_session.query(Material).filter(Material.id == mid).delete(synchronize_session=False)
    db_session.commit()
