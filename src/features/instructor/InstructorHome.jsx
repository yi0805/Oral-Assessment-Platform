import { useNavigate } from "react-router";
import { useState } from "react";

import { useCourses } from "../../hooks/useCourses";
import { usePendingReviews } from "./usePendingReviews";
import { useCreateCourse } from "./useCreateCourse";

import InstructorCourseCard from "../../ui/InstructorCourseCard";
import Spinner from "../../ui/Spinner";
import { courseCodeRegex } from "../../utils/constants";

function InstructorHome() {
  const navigate = useNavigate();

  const [showCourseModal, setShowCourseModal] = useState(false);

  const [courseCode, setCourseCode] = useState("");
  const [courseName, setCourseName] = useState("");
  const [description, setDescription] = useState("");

  const [courseCodeError, setCourseCodeError] = useState("");
  const [courseNameError, setCourseNameError] = useState("");
  const [courseDescriptionError, setCourseDescriptionError] = useState("");

  const { courses, isLoading } = useCourses();
  const { createCourse, isPending } = useCreateCourse();

  const { pendingReviews, isLoading: isPendingReviewsLoading } =
    usePendingReviews();

  if (isLoading || isPendingReviewsLoading) return <Spinner />;

  function handleSubmit() {
    const trimmedCourseCode = courseCode.trim();
    const trimmedCourseName = courseName.trim();
    const trimmedDescription = description.trim();

    if (!trimmedCourseName) {
      setCourseNameError("Course name cannot be empty");
      return;
    }

    if (!trimmedDescription) {
      setCourseDescriptionError("Course description cannot be empty");
      return;
    }

    if (!courseCodeRegex.test(trimmedCourseCode)) {
      setCourseCodeError("Use format like COMPSCI 101");
      return;
    }

    createCourse(
      {
        course_code: trimmedCourseCode,
        course_name: trimmedCourseName,
        description: trimmedDescription,
      },
      {
        onSuccess: () => {
          setCourseCode("");
          setCourseName("");
          setDescription("");
          setCourseCodeError("");
          setShowCourseModal(false);
        },
      },
    );
  }

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
                    {pendingReviews.length}
                  </h2>
                </div>

                <div className="hidden h-10 w-[1px] bg-outline-variant/20 md:block"></div>
                {pendingReviews.length > 0 ? (
                  <p className="max-w-sm font-body text-sm text-on-surface-variant">
                    Student submissions are currently awaiting your feedback and
                    grading.
                  </p>
                ) : (
                  <p className="max-w-sm font-body text-sm text-on-surface-variant">
                    No pending reviews at the moment.
                  </p>
                )}
              </div>

              <div className="flex w-full flex-row gap-3 md:w-auto">
                <button
                  className="flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2 font-headline text-xs font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-95 disabled:opacity-50"
                  onClick={() => {
                    navigate("/instructor/pendingGrades");
                  }}
                  disabled={pendingReviews.length === 0}
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
          onClick={() => setShowCourseModal(true)}
        >
          <span className="material-symbols-outlined text-3xl transition-transform duration-300 group-hover:rotate-90">
            add
          </span>
        </button>
      </div>

      {showCourseModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-inverse-surface/40 p-4 backdrop-blur-sm">
          <div className="animate-in fade-in zoom-in w-full max-w-2xl overflow-hidden rounded-2xl border border-outline-variant/20 bg-surface-container-lowest shadow-2xl duration-300">
            <div className="flex items-center justify-between border-b border-outline-variant/10 p-8">
              <div>
                <h2 className="font-headline text-2xl font-extrabold tracking-tight text-on-surface">
                  Add New Course
                </h2>
              </div>

              <button
                className="rounded-full p-2 text-on-surface-variant transition-colors hover:bg-surface-container-high"
                type="button"
                onClick={() => setShowCourseModal(false)}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="space-y-6 p-8">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <label
                    className="block font-headline text-xs font-bold uppercase tracking-widest text-secondary"
                    htmlFor="course-code"
                  >
                    Course Number
                  </label>
                  <input
                    className="w-full rounded-xl border border-outline-variant/30 bg-surface-container-low px-4 py-3 font-body text-sm outline-none transition-all placeholder:text-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20"
                    id="course-code"
                    placeholder="format: COMPSCI 101"
                    type="text"
                    value={courseCode}
                    onChange={(e) => {
                      setCourseCode(e.target.value.toUpperCase());
                      if (courseCodeError) setCourseCodeError("");
                    }}
                  />
                  {courseCodeError && (
                    <p className="text-sm text-red-500">{courseCodeError}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label
                    className="block font-headline text-xs font-bold uppercase tracking-widest text-secondary"
                    htmlFor="course-name"
                  >
                    Course Name
                  </label>
                  <input
                    className="w-full rounded-xl border border-outline-variant/30 bg-surface-container-low px-4 py-3 font-body text-sm outline-none transition-all placeholder:text-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20"
                    id="course-name"
                    placeholder="e.g. Principles of Programming"
                    type="text"
                    value={courseName}
                    onChange={(e) => {
                      setCourseName(e.target.value);
                      if (courseNameError) setCourseNameError("");
                    }}
                  />
                  {courseNameError && (
                    <p className="text-sm text-red-500">{courseNameError}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label
                  className="block font-headline text-xs font-bold uppercase tracking-widest text-secondary"
                  htmlFor="course-desc"
                >
                  Course Description
                </label>
                <textarea
                  className="min-h-[120px] w-full resize-none rounded-xl border border-outline-variant/30 bg-surface-container-low px-4 py-3 font-body text-sm outline-none transition-all placeholder:text-outline-variant focus:border-primary focus:ring-2 focus:ring-primary/20"
                  id="course-desc"
                  placeholder="Briefly describe the course objectives and learning outcomes..."
                  value={description}
                  onChange={(e) => {
                    setDescription(e.target.value);
                    if (courseDescriptionError) setCourseDescriptionError("");
                  }}
                ></textarea>
                {courseDescriptionError && (
                  <p className="text-sm text-red-500">
                    {courseDescriptionError}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 border-t border-outline-variant/10 bg-surface-container-low p-6">
              <button
                className="rounded-xl px-6 py-2.5 font-headline text-sm font-bold text-secondary transition-all hover:bg-surface-container-high"
                onClick={() => setShowCourseModal(false)}
              >
                Cancel
              </button>
              <button
                className="rounded-xl bg-primary px-8 py-2.5 font-headline text-sm font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-95 disabled:opacity-50"
                type="button"
                onClick={handleSubmit}
                disabled={isPending}
              >
                {isPending ? "Creating..." : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default InstructorHome;
