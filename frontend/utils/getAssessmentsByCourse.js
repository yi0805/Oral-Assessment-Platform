import mockAssessments from "../data/mockAssessments";

function getAssessmentsByCourse(courseId) {
  const courseAssessments = mockAssessments.filter(
    (assessment) => assessment.courseId === courseId,
  );
  return courseAssessments;
}

export default getAssessmentsByCourse;
