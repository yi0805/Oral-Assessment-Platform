import mockAssessments from "../data/mockAssessments";

function getAssessmentByCourseAndStudent(courseId, studentName) {
  return mockAssessments.filter(
    (assessment) =>
      assessment.courseId === courseId &&
      assessment.studentName === studentName &&
      assessment.status === "upcoming",
  );
}

export default getAssessmentByCourseAndStudent;
