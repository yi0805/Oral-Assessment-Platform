import mockAssessmentResults from "../data/mockAssessmentResult";

function getStudentAssessmentResult(completedAssessments) {
  return completedAssessments.map((assessment) => {
    const matchedResult = mockAssessmentResults.find(
      (result) =>
        result.studentName === assessment.studentName &&
        result.courseId === assessment.courseId &&
        result.assessment === assessment.assessment,
    );

    return {
      studentName: assessment.studentName,
      assessment: assessment.assessment,
      grade: matchedResult ? matchedResult.grade : "0",
    };
  });
}

export default getStudentAssessmentResult;
