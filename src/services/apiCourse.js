import api from "./api";

export async function getCourses() {
  const response = await api.get("/courses");
  return response.data;
}

export async function createCourse(course_code, course_name, description) {
  const { data } = await api.post("/courses", {
    course_code: course_code,
    course_name: course_name,
    description: description,
  });

  return data;
}
