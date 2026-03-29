import mockAssessments from "../data/mockAssessments";

function getCompletedAssessmentByStudentandCourse(studentName, selectedCourse) {
  const selectedCourseAssessments = mockAssessments.filter(
    (assessment) =>
      assessment.studentName === studentName &&
      assessment.courseId === selectedCourse,
  );

  const completedAssessments = selectedCourseAssessments.filter(
    (assessment) => assessment.status === "Completed",
  );
  return completedAssessments;
}

export default getCompletedAssessmentByStudentandCourse;
