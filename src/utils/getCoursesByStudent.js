import mockCourses from "../data/mockCourses";

function getCoursesByStudent(student) {
  if (!student) return [];

  return mockCourses.filter((course) => student.course.includes(course.id));
}

export default getCoursesByStudent;
