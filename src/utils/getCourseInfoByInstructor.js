import mockCourses from "../data/mockCourses";

function getCourseInfoByInstructor(instructor) {
  const matchedCourses = instructor.teachingCourses.map((courseId) =>
    mockCourses.find((course) => course.id === courseId),
  );

  return matchedCourses;
}

export default getCourseInfoByInstructor;
