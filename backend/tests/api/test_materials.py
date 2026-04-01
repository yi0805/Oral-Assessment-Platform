"""
Tests for material upload and management endpoints.

POST   /api/v1/courses/{course_id}/materials/upload  → upload a file
GET    /api/v1/courses/{course_id}/materials         → list materials
GET    /api/v1/materials/{material_id}               → get material detail
GET    /api/v1/materials/{material_id}/status        → poll processing status
DELETE /api/v1/materials/{material_id}               → delete material

The material processing pipeline is mocked so tests do not run Gemini or
any file-system background work.  S3 integration tests live in the
separate test_materials_s3_upload.py file.
"""
from __future__ import annotations

import io

# Minimal valid PDF bytes (just enough for the content-type check)
_MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
_MINIMAL_DOCX = b"PK\x03\x04"  # DOCX is a zip; real tests can use fixtures


# ---------------------------------------------------------------------------
# POST /courses/{course_id}/materials/upload
# ---------------------------------------------------------------------------

class TestUploadMaterial:
    def test_instructor_can_upload_pdf(self, client_no_pipeline, instructor_headers, sample_course):
        course_id = sample_course["id"]
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("lecture.pdf", _MINIMAL_PDF, "application/pdf")},
            data={"title": "Week 1 Lecture"},
            headers=instructor_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Week 1 Lecture"
        assert body["original_filename"] == "lecture.pdf"
        assert body["file_type"] == "pdf"
        assert body["processing_status"] == "uploaded"
        assert "id" in body

    def test_upload_uses_filename_as_default_title(self, client_no_pipeline, instructor_headers, sample_course):
        course_id = sample_course["id"]
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("auto_title.pdf", _MINIMAL_PDF, "application/pdf")},
            headers=instructor_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        # Title should default to something (not empty)
        assert body["title"]

    def test_student_cannot_upload(self, client_no_pipeline, student_headers, sample_course):
        course_id = sample_course["id"]
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("lecture.pdf", _MINIMAL_PDF, "application/pdf")},
            headers=student_headers,
        )
        assert resp.status_code == 403

    def test_unsupported_file_type_returns_400(self, client_no_pipeline, instructor_headers, sample_course):
        course_id = sample_course["id"]
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
            data={"title": "Bad File"},
            headers=instructor_headers,
        )
        assert resp.status_code in (400, 422)

    def test_upload_to_nonexistent_course_returns_404(self, client_no_pipeline, instructor_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{fake_id}/materials/upload",
            files={"file": ("lecture.pdf", _MINIMAL_PDF, "application/pdf")},
            data={"title": "Orphan"},
            headers=instructor_headers,
        )
        assert resp.status_code == 404

    def test_unauthenticated_upload_returns_401_403(self, client_no_pipeline, sample_course):
        course_id = sample_course["id"]
        resp = client_no_pipeline.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("lecture.pdf", _MINIMAL_PDF, "application/pdf")},
        )
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /courses/{course_id}/materials
# ---------------------------------------------------------------------------

class TestListMaterials:
    def _upload(self, client, headers, course_id, filename="lec.pdf"):
        return client.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": (filename, _MINIMAL_PDF, "application/pdf")},
            data={"title": filename},
            headers=headers,
        )

    def test_returns_paginated_response(self, client_no_pipeline, instructor_headers, sample_course):
        self._upload(client_no_pipeline, instructor_headers, sample_course["id"])
        resp = client_no_pipeline.get(
            f"/api/v1/courses/{sample_course['id']}/materials",
            headers=instructor_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        for key in ("items", "total", "page", "page_size", "total_pages"):
            assert key in body

    def test_uploaded_material_appears_in_list(self, client_no_pipeline, instructor_headers, sample_course):
        self._upload(client_no_pipeline, instructor_headers, sample_course["id"], "specific.pdf")
        resp = client_no_pipeline.get(
            f"/api/v1/courses/{sample_course['id']}/materials",
            headers=instructor_headers,
        )
        titles = [m["title"] for m in resp.json()["items"]]
        assert "specific.pdf" in titles

    def test_empty_course_returns_empty_list(self, client, instructor_headers, sample_course):
        resp = client.get(
            f"/api/v1/courses/{sample_course['id']}/materials",
            headers=instructor_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_non_enrolled_cannot_list_materials(self, client_no_pipeline, student_headers, sample_course):
        resp = client_no_pipeline.get(
            f"/api/v1/courses/{sample_course['id']}/materials",
            headers=student_headers,
        )
        # Student is not enrolled in sample_course, so they should get 403
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /materials/{material_id} and /materials/{material_id}/status
# ---------------------------------------------------------------------------

class TestGetMaterial:
    def _upload_and_get_id(self, client, headers, course_id):
        resp = client.post(
            f"/api/v1/courses/{course_id}/materials/upload",
            files={"file": ("lec.pdf", _MINIMAL_PDF, "application/pdf")},
            data={"title": "Detail Test"},
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_get_material_detail(self, client_no_pipeline, instructor_headers, sample_course):
        mid = self._upload_and_get_id(client_no_pipeline, instructor_headers, sample_course["id"])
        resp = client_no_pipeline.get(f"/api/v1/materials/{mid}", headers=instructor_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == mid
        assert body["title"] == "Detail Test"

    def test_status_endpoint(self, client_no_pipeline, instructor_headers, sample_course):
        mid = self._upload_and_get_id(client_no_pipeline, instructor_headers, sample_course["id"])
        resp = client_no_pipeline.get(f"/api/v1/materials/{mid}/status", headers=instructor_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "processing_status" in body
        assert body["processing_status"] in (
            "uploaded", "extracting", "chunking", "embedding", "ready", "failed"
        )

    def test_nonexistent_material_returns_404(self, client, instructor_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/api/v1/materials/{fake_id}", headers=instructor_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /materials/{material_id}
# ---------------------------------------------------------------------------

class TestDeleteMaterial:
    def test_instructor_can_delete_material(self, client_no_pipeline, instructor_headers, sample_course):
        mid_resp = client_no_pipeline.post(
            f"/api/v1/courses/{sample_course['id']}/materials/upload",
            files={"file": ("del.pdf", _MINIMAL_PDF, "application/pdf")},
            data={"title": "To Delete"},
            headers=instructor_headers,
        )
        mid = mid_resp.json()["id"]

        del_resp = client_no_pipeline.delete(f"/api/v1/materials/{mid}", headers=instructor_headers)
        assert del_resp.status_code in (200, 204)

        # Confirm it's gone
        get_resp = client_no_pipeline.get(f"/api/v1/materials/{mid}", headers=instructor_headers)
        assert get_resp.status_code == 404

    def test_student_cannot_delete_material(self, client_no_pipeline, instructor_headers, student_headers, sample_course):
        mid_resp = client_no_pipeline.post(
            f"/api/v1/courses/{sample_course['id']}/materials/upload",
            files={"file": ("nodelete.pdf", _MINIMAL_PDF, "application/pdf")},
            data={"title": "Protected"},
            headers=instructor_headers,
        )
        mid = mid_resp.json()["id"]
        del_resp = client_no_pipeline.delete(f"/api/v1/materials/{mid}", headers=student_headers)
        assert del_resp.status_code == 403
