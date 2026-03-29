import mockInstructor from "../data/mockInstructor";

function getInstructorByName(userName) {
  return mockInstructor.find(
    (instructor) => instructor.instructorName === userName,
  );
}

export default getInstructorByName;
