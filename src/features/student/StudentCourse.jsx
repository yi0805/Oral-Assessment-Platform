import { useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router";

import getAssessmentByCourseAndStudent from "../../utils/getAssessmentByCourseAndStudent";
import getEarliestAssessment from "../../utils/getEarliestAssessment";

export default function StudentCourse() {
  const [isOpen, setIsOpen] = useState(false);
  const [assessmentId, setAssessmentId] = useState(null);
  const navigate = useNavigate();

  const { studentName, courseId } = useLocation().state || {};

  const assessments = getAssessmentByCourseAndStudent(courseId, studentName);
  const earliestDeadline = getEarliestAssessment(assessments);

  const sortedAssessments = [...assessments].sort(
    (a, b) => new Date(a.deadline) - new Date(b.deadline),
  );

  return (
    <>
      <main className="ml-64 min-h-screen px-12 pb-12 pt-24">
        <div className="mb-10">
          <NavLink
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
            to="/home"
          >
            <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>
            <span className="font-body uppercase tracking-widest">
              Back to Courses
            </span>
          </NavLink>

          <span className="mb-1 block text-xs font-semibold uppercase tracking-widest text-outline">
            Assessments
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight text-on-background">
            {courseId}
          </h1>
        </div>

        <div className="mb-8 flex items-end justify-between">
          <div className="flex gap-4">
            <button className="flex items-center gap-2 rounded-full bg-surface-container-highest px-4 py-2 text-xs font-bold text-primary">
              UPCOMING
            </button>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-on-surface-variant">
              Next Deadline:
              <span className="font-bold text-error"> {earliestDeadline}</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {sortedAssessments.map((assessment, index) => {
            if (index === 0) {
              return (
                <div
                  key={index}
                  className="group col-span-12 cursor-pointer lg:col-span-8"
                  onClick={() => {
                    setIsOpen(true);
                    setAssessmentId(assessment.assessment);
                  }}
                >
                  <div className="relative flex h-full flex-col justify-between overflow-hidden rounded-xl bg-surface-container-lowest p-8 transition-all hover:shadow-2xl hover:shadow-primary/5">
                    <div className="absolute right-0 top-0 p-8">
                      <span className="rounded-full bg-error/10 px-3 py-1 text-[10px] font-bold tracking-wider text-error">
                        DUE SOON
                      </span>
                    </div>

                    <div>
                      <span
                        className="material-symbols-outlined mb-4 text-4xl text-primary"
                        style={{ fontVariationSettings: '"FILL" 1' }}
                      >
                        analytics
                      </span>
                      <h2 className="mb-2 text-2xl font-bold text-on-surface">
                        {assessment.assessment}
                      </h2>
                      <p className="max-w-md text-sm leading-relaxed text-on-surface-variant">
                        {assessment.summary}
                      </p>
                    </div>
                    <div className="mt-12 flex items-center justify-between">
                      <div className="flex gap-8">
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-outline">
                            Duration
                          </span>
                          <span className="text-sm font-semibold text-on-surface">
                            {assessment.duration}
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-outline">
                            Questions
                          </span>
                          <span className="text-sm font-semibold text-on-surface">
                            {assessment.questionNumbers}
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-outline">
                            Weight
                          </span>
                          <span className="text-sm font-semibold text-on-surface">
                            {assessment.grade} Final Grade
                          </span>
                        </div>
                      </div>
                      <button className="flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-xs font-bold text-on-primary transition-transform group-hover:translate-x-1">
                        START NOW
                        <span className="material-symbols-outlined text-sm">
                          arrow_forward
                        </span>
                      </button>
                    </div>

                    <div className="absolute -bottom-10 -right-10 opacity-5 transition-opacity group-hover:opacity-10">
                      <span className="material-symbols-outlined text-[200px]">
                        history_edu
                      </span>
                    </div>
                  </div>
                </div>
              );
            }

            if (index === 1) {
              return (
                <div
                  key={index}
                  className="group col-span-12 cursor-pointer lg:col-span-4"
                  onClick={() => {
                    setIsOpen(true);
                    setAssessmentId(assessment.assessment);
                  }}
                >
                  <div className="flex h-full flex-col justify-between rounded-xl border border-transparent bg-surface-container-lowest p-6 transition-all hover:border-outline-variant/10 hover:shadow-xl hover:shadow-primary/5">
                    <div>
                      <div className="mb-6 flex items-start justify-between">
                        <span className="material-symbols-outlined text-2xl text-secondary">
                          database
                        </span>
                        <span className="rounded bg-primary-container px-2 py-1 text-[10px] font-bold text-on-primary-container">
                          {assessment.deadline}
                        </span>
                      </div>
                      <h3 className="mb-2 text-lg font-bold text-on-surface">
                        {assessment.assessment}
                      </h3>
                      <p className="text-xs leading-relaxed text-on-surface-variant">
                        {assessment.summary}
                      </p>
                    </div>
                    <div className="mt-8">
                      <div className="mb-4 h-1.5 w-full rounded-full bg-surface-container">
                        <div className="h-1.5 w-0 rounded-full bg-primary transition-all duration-1000"></div>
                      </div>
                      <div className="flex items-center justify-between text-[10px] font-bold text-outline"></div>
                    </div>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={index}
                className="group col-span-12 cursor-pointer md:col-span-4 lg:col-span-3"
                onClick={() => {
                  setIsOpen(true);
                  setAssessmentId(assessment.assessment);
                }}
              >
                <div className="rounded-xl border border-transparent bg-surface-container-lowest p-6 transition-all hover:border-outline-variant/10 hover:shadow-lg">
                  <span className="material-symbols-outlined mb-4 text-primary">
                    menu_book
                  </span>
                  <h3 className="mb-1 font-bold text-on-surface">
                    {assessment.assessment}
                  </h3>
                  <p className="mb-6 text-xs text-on-surface-variant">
                    {assessment.summary}
                  </p>
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-outline">
                    <span className="material-symbols-outlined text-sm">
                      schedule
                    </span>
                    {assessment.duration}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-on-background/40 backdrop-blur-md"
          id="modal-overlay"
        >
          <div className="relative w-full max-w-md overflow-hidden rounded-2xl bg-surface-container-lowest p-10 shadow-2xl">
            <div className="absolute left-0 top-0 h-1.5 w-full bg-primary"></div>
            <div className="mb-8 text-center">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary-container text-primary">
                <span
                  className="material-symbols-outlined text-3xl"
                  style={{ fontVariationSettings: '"FILL" 1' }}
                >
                  timer
                </span>
              </div>
              <h2 className="mb-2 text-2xl font-bold text-on-surface">
                Ready to begin?
              </h2>
              <p className="px-4 text-sm text-on-surface-variant">
                Once you start the assessment, you will only have one attempt to
                complete it. Please make sure you have a stable internet
                connection before starting.
              </p>
            </div>
            <div className="mb-10 space-y-4">
              <div className="flex items-center gap-4 rounded-xl bg-surface-container-low p-4">
                <span className="material-symbols-outlined text-primary">
                  check_circle
                </span>
                <div className="text-left">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-outline">
                    Attempt No.
                  </p>
                  <p className="text-sm font-semibold">1 of 1</p>
                </div>
              </div>
              <div className="flex items-center gap-4 rounded-xl bg-surface-container-low p-4">
                <span className="material-symbols-outlined text-primary">
                  verified_user
                </span>
                <div className="text-left">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-outline">
                    Integrity Check
                  </p>
                  <p className="text-sm font-semibold">
                    Plagiarism detection enabled
                  </p>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-3">
              <button
                className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-95"
                onClick={() =>
                  navigate(`/student/${courseId}/${assessmentId}`, {
                    state: {
                      studentName,
                      courseId,
                      assessmentId,
                    },
                  })
                }
              >
                START ASSESSMENT
              </button>
              <button
                className="w-full rounded-xl bg-transparent py-3 text-sm font-semibold text-outline-variant transition-all hover:bg-surface-container"
                onClick={() => setIsOpen(false)}
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
