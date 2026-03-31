import { useState } from "react";

import getStudentByName from "../../utils/getStudentByname";
import getCoursesByStudent from "../../utils/getCoursesByStudent";
import CourseSelector from "../../ui/CourseSelector";
import getCompletedAssessmentByStudentandCourse from "../../utils/getCompletedAssessmentByStudentandCourse";
import getStudentAssessmentResult from "../../utils/getStudentAssessmentGrade";
import getStudentAvgAssessmentGrade from "../../utils/getStudentAvgAssessmentGrade";
import getClassAvgGrade from "../../utils/getClassAvgGrade";
import InstructorFeedback from "../../ui/InstructorFeedback";

function StudentPreviousAssessment() {
  const userName = localStorage.getItem("userName");

  const student = getStudentByName(userName);
  const courses = student ? getCoursesByStudent(student) : [];

  const [selectedCourse, setSelectedCourse] = useState(courses[0]?.id || "");

  const completedAssessments = getCompletedAssessmentByStudentandCourse(
    student.studentName,
    selectedCourse,
  );

  const studentAssessmentResults =
    getStudentAssessmentResult(completedAssessments);

  // improve here later
  if (studentAssessmentResults.length === 0) {
    return (
      <main className="ml-64 min-h-screen px-12 pb-12 pt-24">
        <p className="text-lg font-semibold text-red-700">
          No assessments found for this course.
        </p>
      </main>
    );
  }

  const averageGrade = getStudentAvgAssessmentGrade(studentAssessmentResults);

  const classAverageGrade = getClassAvgGrade(selectedCourse);
  const difference = averageGrade - classAverageGrade;
  const classAverageGradeText = `${difference >= 0 ? "+" : "-"}${difference.toFixed(1)}`;

  const bestAssessmentGrade = Math.max(
    ...studentAssessmentResults.map((assessment) => assessment.grade),
  );
  const lowestAssessmentGrade = Math.min(
    ...studentAssessmentResults.map((assessment) => assessment.grade),
  );

  const bestAssessmentName = studentAssessmentResults.find(
    (assessment) => parseInt(assessment.grade) === bestAssessmentGrade,
  ).assessment;
  const lowestAssessmentName = studentAssessmentResults.find(
    (assessment) => parseInt(assessment.grade) === lowestAssessmentGrade,
  ).assessment;

  return (
    <div className="min-h-screen">
      <main className="px-8 pb-12 pt-24 md:ml-64">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10">
            <span className="text-xs font-medium uppercase tracking-widest text-outline">
              Performance History
            </span>
            <h1 className="mt-1 text-4xl font-extrabold tracking-tight text-on-surface">
              Previous Assessments
            </h1>

            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm font-semibold text-on-surface-variant">
                Course:
              </span>

              <CourseSelector
                courses={courses}
                selectedCourse={selectedCourse}
                onChange={setSelectedCourse}
              />
            </div>
          </div>

          <section className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8 shadow-sm">
              <div>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-container">
                  <span className="material-symbols-outlined text-on-primary-container">
                    analytics
                  </span>
                </div>
                <p className="text-sm font-medium text-on-surface-variant">
                  Course Average
                </p>
              </div>
              <div className="mt-4">
                <span className="text-4xl font-bold text-primary">
                  {averageGrade.toFixed(1)} / 10
                </span>
                <span className="ml-2 text-xs font-medium text-secondary">
                  {classAverageGradeText} vs. Class Avg
                </span>
              </div>
            </div>
            <div className="flex flex-col justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8 shadow-sm">
              <div>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-tertiary-container">
                  <span className="material-symbols-outlined text-on-tertiary-container">
                    emoji_events
                  </span>
                </div>
                <p className="text-sm font-medium text-on-surface-variant">
                  Highest Score
                </p>
              </div>
              <div className="mt-4">
                <span className="text-4xl font-bold text-on-surface">
                  {bestAssessmentGrade}
                </span>
                <p className="mt-1 text-xs text-on-surface-variant">
                  {bestAssessmentName}
                </p>
              </div>
            </div>
            <div className="flex flex-col justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8 shadow-sm">
              <div>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-surface-container-highest">
                  <span className="material-symbols-outlined text-on-surface-variant">
                    trending_down
                  </span>
                </div>
                <p className="text-sm font-medium text-on-surface-variant">
                  Lowest Score
                </p>
              </div>
              <div className="mt-4">
                <span className="text-4xl font-bold text-on-surface">
                  {lowestAssessmentGrade}
                </span>
                <p className="mt-1 text-xs text-on-surface-variant">
                  {lowestAssessmentName}
                </p>
              </div>
            </div>
          </section>

          <section className="mb-12">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-xl font-bold text-on-surface">
                Course Submissions
              </h3>
            </div>

            <div className="overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm">
              <div className="grid grid-cols-12 bg-surface-container-low px-6 py-4 text-xs font-bold uppercase tracking-wider text-outline">
                <div className="col-span-5">Assessment Title</div>
                <div className="col-span-2">Date Submitted</div>
                <div className="col-span-2 text-center">Weight</div>
                <div className="col-span-2 text-center">Score</div>
              </div>

              {studentAssessmentResults.map((assessment, index) => (
                <div
                  key={assessment.assessment}
                  className={`group grid cursor-pointer grid-cols-12 items-center px-6 py-6 transition-colors hover:bg-surface-container-low ${
                    index !== 0 ? "border-t border-surface-container" : ""
                  }`}
                >
                  <div className="col-span-5">
                    <p className="font-semibold text-on-surface">
                      {assessment.assessment}
                    </p>
                  </div>

                  <div className="col-span-2 text-sm text-on-surface-variant">
                    {assessment.submittedDate}
                  </div>

                  <div className="col-span-2 text-center">
                    <span className="rounded-full bg-surface-container px-2 py-1 text-xs text-on-surface-variant">
                      {assessment.weight}
                    </span>
                  </div>

                  <div className="col-span-2 text-center">
                    <span
                      className={`text-lg font-bold ${
                        index === 0 ? "text-primary" : "text-on-surface-variant"
                      }`}
                    >
                      {assessment.grade}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <InstructorFeedback
            studentAssessmentResults={studentAssessmentResults}
          />
        </div>
      </main>
    </div>
  );
}

export default StudentPreviousAssessment;
