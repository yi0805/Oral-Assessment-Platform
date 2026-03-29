import mockAssessmentResults from "../data/mockAssessmentResult";


function getUngradedAssessmentsByInstructor(instructor) {
    return mockAssessmentResults.filter(
        (assessment) =>
          assessment.status === "ungraded" &&
          instructor.teachingCourses.includes(assessment.courseId),
      );
}

export default getUngradedAssessmentsByInstructor;