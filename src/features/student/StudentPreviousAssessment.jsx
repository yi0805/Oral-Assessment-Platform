import { useEffect, useState } from "react";

import { useCourses } from "../../hooks/useCourses";
import { useAssessmentHistory } from "./useAssessmentHistory";

import Spinner from "../../ui/Spinner";
import InstructorFeedback from "../../ui/InstructorFeedback";
import CourseSelector from "../../ui/CourseSelector";

function StudentPreviousAssessment() {
  const [selectedCourse, setSelectedCourse] = useState("");

  const { courses, isLoading: coursesLoading } = useCourses();

  useEffect(() => {
    if (courses.length > 0 && !selectedCourse) {
      setSelectedCourse(courses[0].id);
    }
  }, [courses, selectedCourse]);

  const { history, isLoading } = useAssessmentHistory(selectedCourse);

  if (coursesLoading) return <Spinner />;
  if (selectedCourse && isLoading) return <Spinner />;

  const items = history?.items ?? [];

  const assessmentResults = items.map((item) => ({
    sessionId: item.session_id,
    title: item.assessment_title,
    grade: item.final_grade.toFixed(1),
    submittedDate: item.submitted_at
      ? new Date(item.submitted_at).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      : "N/A",
    feedback: item.comments ?? "No feedback available.",
    instructorName: item.instructor_name,
    instructorImage: item.instructor_image,
    department: "Computer Science",
  }));

  const Grades = items.map((i) => i.final_grade);

  const studentAvg =
    Grades.length > 0 ? Grades.reduce((s, g) => s + g, 0) / Grades.length : 0;
  const classAvg =
    history?.class_average_grade != null ? history.class_average_grade : null;

  const diff = classAvg != null ? studentAvg - classAvg : null;
  const classAverageGradeText =
    diff != null
      ? `${diff >= 0 ? "+" : ""}${diff.toFixed(1)} vs. Class Avg`
      : "";

  const bestGrade = Grades.length > 0 ? Math.max(...Grades) : null;
  const lowestGrade = Grades.length > 0 ? Math.min(...Grades) : null;

  const bestAssessmentName =
    bestGrade != null
      ? (assessmentResults.find((a) => Number(a.grade) === bestGrade)?.title ??
        "—")
      : "—";

  const lowestAssessmentName =
    lowestGrade != null
      ? (assessmentResults.find((a) => Number(a.grade) === lowestGrade)
          ?.title ?? "—")
      : "—";

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

          {assessmentResults.length === 0 ? (
            <div className="flex flex-col items-center gap-4 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-12 text-center shadow-sm">
              <span className="material-symbols-outlined text-6xl text-on-surface-variant">
                sentiment_dissatisfied
              </span>

              <p className="text-lg font-medium text-on-surface">
                No previous assessments found.
              </p>
            </div>
          ) : (
            <>
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
                      {studentAvg.toFixed(1)} / 100
                    </span>

                    {classAverageGradeText && (
                      <span className="ml-2 text-xs font-medium text-secondary">
                        {classAverageGradeText}
                      </span>
                    )}
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
                      {bestGrade != null ? bestGrade.toFixed(1) : "—"}
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
                      {lowestGrade != null ? lowestGrade.toFixed(1) : "—"}
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
                    <div className="col-span-7">Assessment Title</div>
                    <div className="col-span-3">Date Submitted</div>
                    <div className="col-span-2 text-center">Score</div>
                  </div>

                  {assessmentResults.map((assessment, index) => (
                    <div
                      key={assessment.sessionId}
                      className={`group grid cursor-pointer grid-cols-12 items-center px-6 py-6 transition-colors hover:bg-surface-container-low ${
                        index !== 0 ? "border-t border-surface-container" : ""
                      }`}
                    >
                      <div className="col-span-7">
                        <p className="font-semibold text-on-surface">
                          {assessment.title}
                        </p>
                      </div>

                      <div className="col-span-3 text-sm text-on-surface-variant">
                        {assessment.submittedDate}
                      </div>

                      <div className="col-span-2 text-center">
                        <span
                          className={`text-lg font-bold ${
                            index === 0
                              ? "text-primary"
                              : "text-on-surface-variant"
                          }`}
                        >
                          {assessment.grade}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <InstructorFeedback assessmentResults={assessmentResults} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default StudentPreviousAssessment;
