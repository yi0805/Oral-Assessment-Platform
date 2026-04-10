function getStudentAvgAssessmentGrade(studentAssessmentResults) {
  const totalScore = studentAssessmentResults.reduce((sum, assessment) => {
    return sum + parseInt(assessment.grade, 10);
  }, 0);

  if (studentAssessmentResults.length === 0) {
    return 0;
  }

  return totalScore / studentAssessmentResults.length;
}

export default getStudentAvgAssessmentGrade;
