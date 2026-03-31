import { useNavigate } from "react-router";

import getInstructorByName from "../../utils/getInstructorByname";
import getUngradedAssessmentsByInstructor from "../../utils/getUngradedAssessmentsByInstructor";
import InstructorCourseCard from "../../ui/InstructorCourseCard";
import getCourseInfoByInstructor from "../../utils/getCourseInfoByInstructor";

function InstructorHome() {
  const navigate = useNavigate();

  const Username = localStorage.getItem("userName");
  const instructor = getInstructorByName(Username);
  const courses = getCourseInfoByInstructor(instructor);

  const unGradedAssessments = getUngradedAssessmentsByInstructor(instructor);

  return (
    <>
      <main className="min-h-screen bg-surface pl-64 pt-24">
        <div className="mx-auto max-w-7xl px-10 pb-20">
          <header className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div>
              <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
                My Courses
              </h1>
            </div>
          </header>

          <div className="mb-10">
            <div className="flex flex-col items-center justify-between gap-6 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-5 shadow-sm md:flex-row md:p-6">
              <div className="flex items-center gap-6">
                <div className="flex flex-col">
                  <div className="mb-1 flex items-center gap-2">
                    <span className="material-symbols-outlined text-lg text-error">
                      assignment_late
                    </span>
                    <span className="font-headline text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                      Pending Reviews
                    </span>
                  </div>
                  <h2 className="text-center font-headline text-4xl font-extrabold leading-none tracking-tight text-primary">
                    {unGradedAssessments.length}
                  </h2>
                </div>
                <div className="hidden h-10 w-[1px] bg-outline-variant/20 md:block"></div>
                <p className="max-w-sm font-body text-sm text-on-surface-variant">
                  Student submissions are currently awaiting your feedback and
                  grading.
                </p>
              </div>
              <div className="flex w-full flex-row gap-3 md:w-auto">
                <button
                  className="flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2 font-headline text-xs font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-95"
                  onClick={() => {
                    navigate("/instructor/pendingGrades", {
                      state: {
                        unGradedAssessments,
                      },
                    });
                  }}
                >
                  Review Submissions
                  <span className="material-symbols-outlined text-xs">
                    arrow_forward
                  </span>
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            <InstructorCourseCard courses={courses} />
          </div>
        </div>
      </main>
      <div className="fixed bottom-8 right-8 z-50">
        <button
          className="group flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-on-primary shadow-2xl transition-all hover:bg-primary-dim active:scale-90"
          // onClick={() => {
          //   navigate("/instructor/AddCourse")
          // }}
        >
          <span className="material-symbols-outlined text-3xl transition-transform duration-300 group-hover:rotate-90">
            add
          </span>
        </button>
      </div>
    </>
  );
}

export default InstructorHome;
