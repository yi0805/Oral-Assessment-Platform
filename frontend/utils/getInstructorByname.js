import mockInstructor from "../data/mockInstructor";

function getInstructorByName(userName) {
  return mockInstructor.find(
    (instructor) => instructor.name === userName,
  );
}

export default getInstructorByName;
