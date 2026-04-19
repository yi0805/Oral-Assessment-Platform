import mockAssessmentResults from "../data/mockAssessmentResult";

function getClassAvgGrade(courseId) {
  const classAverage =
    mockAssessmentResults
      .filter((result) => result.courseId === courseId)
      .reduce((sum, result) => sum + parseInt(result.grade, 10), 0) /
    mockAssessmentResults.filter((result) => result.courseId === courseId)
      .length;

  if (
    mockAssessmentResults.filter((result) => result.courseId === courseId)
      .length === 0
  ) {
    return 0;
  }

  return classAverage;
}

export default getClassAvgGrade;
