import mockAssessmentResults from "../data/mockAssessmentResult";

function getNumberofAssessmentsByCourseandAssessment(
  selectedAssessment,
  courseId,
) {
  const numberofAsesssments = mockAssessmentResults.filter(
    (assessment) =>
      assessment.assessment === selectedAssessment &&
      assessment.courseId === courseId,
  );
  return numberofAsesssments.length;
}

export default getNumberofAssessmentsByCourseandAssessment;
