import mockCourses from "../data/mockCourses";

function getCoursesByInstructor(Instructor) {
  if (!Instructor) return [];

  return mockCourses.filter((course) => Instructor.courses.includes(course.id));
}

export default getCoursesByInstructor;