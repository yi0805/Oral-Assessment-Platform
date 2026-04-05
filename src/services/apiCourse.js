import api from "./api";

export async function getCourses() {
  const response = await api.get("/courses");
  return response.data;
}

export async function createCourse(course_code, course_name, description) {
  const response = await api.post("/courses", {
    course_code: course_code,
    course_name: course_name,
    description: description,
  });

  return response.data;
}

export async function getDashboard(courseId) {
  const response = await api.get(`/courses/${courseId}/instructor/dashboard`);

  return response.data;
}
