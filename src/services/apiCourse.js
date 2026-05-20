import api from "./api";

export async function getCourses() {
  const response = await api.get("/courses");
  return response.data;
}

export async function createCourse(course_code, course_name, term, description) {
  const response = await api.post("/courses", {
    course_code: course_code,
    course_name: course_name,
    term: term,
    description: description,
  });

  return response.data;
}

export async function getJoinRequests() {
  const response = await api.get("/courses/join-requests");
  return response.data;
}

export async function createJoinRequest(courseId) {
  const response = await api.post(`/courses/${courseId}/join-request`);
  return response.data;
}

export async function approveJoinRequest(requestId) {
  const response = await api.post(
    `/courses/join-requests/${requestId}/approve`,
  );
  return response.data;
}

export async function rejectJoinRequest(requestId) {
  const response = await api.post(
    `/courses/join-requests/${requestId}/reject`,
  );
  return response.data;
}

export async function dismissJoinRequest(requestId) {
  const response = await api.delete(`/courses/join-requests/${requestId}`);
  return response.data;
}

export async function getDashboard(courseId) {
  const response = await api.get(`/courses/${courseId}/instructor/dashboard`);

  return response.data;
}

export async function importStudentsCSV(courseId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(
    `/courses/${courseId}/students/import-csv`,
    formData,
  );

  return response.data;
}

export async function exportResultsCSV(courseId, assessmentConfigId) {
  const response = await api.get(
    `/courses/${courseId}/assessments/${assessmentConfigId}/export-results`,
    { responseType: "blob" },
  );

  return response;
}

export async function enrolUser(courseId, upi, role) {
  const response = await api.post(`/courses/${courseId}/enroluser`, {
    upi,
    role,
  });

  return response.data;
}

export async function deleteEnrolment(courseId, upi, role) {
  const response = await api.delete(`/courses/${courseId}/delete-enrolment`, {
    data: { upi, role },
  });

  return response.data;
}

export async function getCourseAssessments(courseId) {
  const response = await api.get(`/courses/${courseId}/assessments`);
  return response.data;
}

export async function getAssessmentDetail(courseId, assessmentConfigId) {
  const response = await api.get(
    `/courses/${courseId}/assessments/${assessmentConfigId}`,
  );
  return response.data;
}

export async function updateAssessmentConfig(
  courseId,
  assessmentConfigId,
  payload,
) {
  const response = await api.put(
    `/courses/${courseId}/assessments/${assessmentConfigId}`,
    payload,
  );
  return response.data;
}

export async function deleteAssessmentConfig(courseId, assessmentConfigId) {
  const response = await api.delete(
    `/courses/${courseId}/assessments/${assessmentConfigId}`,
  );
  return response.data;
}

export async function copyAssessmentConfig(courseId, assessmentConfigId, targetCourseId, title) {
  const response = await api.post(
    `/courses/${courseId}/assessments/${assessmentConfigId}/copy`,
    { target_course_id: targetCourseId, title: title || undefined },
  );
  return response.data;
}

export async function listEnrolledUser(courseId) {
  const response = await api.get(
    `/courses/${courseId}/enrolledusers`,
  );
  return response.data;
}