import { NavLink } from "react-router";
import { useEffect, useState } from "react";

import { usePendingReviews } from "./usePendingReviews";
import { useReleaseAllResults } from "./useReleaseAllResults";
import { useApproveAllAiGrades } from "./useApproveAllAiGrades";

import PendingStudentTable from "../../ui/PendingStudentTable";
import Spinner from "../../ui/Spinner";

function InstructorPendingGrades() {
  const [searchValue, setSearchValue] = useState("");
  const [grades, setGrades] = useState({});

  const { pendingReviews, isLoading } = usePendingReviews();
  const { releaseAllResults } = useReleaseAllResults();
  const { approveAllAiGrades, isPending: isApprovingAll } =
    useApproveAllAiGrades();

  useEffect(() => {
    if (!pendingReviews) return;

    setGrades((prev) => {
      const next = { ...prev };
      for (const review of pendingReviews) {
        const sessionId = review.session.id;
        const grade = review.session_feedback?.final_grade;
        if (grade != null) {
          next[sessionId] = String(grade);
        }
      }
      return next;
    });
  }, [pendingReviews]);

  if (isLoading) return <Spinner />;

  const extractedReviews = pendingReviews.map((review) => {
    const sessionId = review.session.id;
    const studentId = review.session.user_s_id;

    const email = review.user.email;
    const fullName = review.user.full_name;
    const image = review.user.image;

    const courseCode = review.course.course_code;
    const title = review.assessment_config.title;

    const suggestedGrade = review.aisummary?.suggested_grade;
    const instructorGrade = review.session_feedback?.final_grade;

    return {
      sessionId,
      studentId,
      email,
      fullName,
      image,
      courseCode,
      title,
      suggestedGrade,
      instructorGrade,
    };
  });

  const filteredReviews = extractedReviews.filter((item) => {
    const keyword = searchValue.toLowerCase().trim();

    const studentName = item.fullName?.toLowerCase() || "";
    const courseCode = item.courseCode?.toLowerCase() || "";

    return studentName.includes(keyword) || courseCode.includes(keyword);
  });

  function handleGradeChange(sessionId, grade) {
    setGrades((prev) => ({
      ...prev,
      [sessionId]: grade,
    }));
  }

  function isValidGrade(grade) {
    if (grade == null || String(grade).trim() === "") return false;

    const numericGrade = Number(grade);
    return (
      Number.isInteger(numericGrade) && numericGrade >= 0 && numericGrade <= 100
    );
  }

  const canPublishAll =
    filteredReviews.length > 0 &&
    filteredReviews.every((review) =>
      isValidGrade(grades[review.sessionId] ?? ""),
    );

  const reviewsWithAiGrade = filteredReviews.filter(
    (r) => r.suggestedGrade != null,
  );
  const canAcceptAllAi = reviewsWithAiGrade.length > 0;

  function handleAcceptAllAi() {
    if (!canAcceptAllAi) return;

    const assessments = reviewsWithAiGrade.map((review) => ({
      session_id: review.sessionId,
    }));
    approveAllAiGrades({ assessments });
  }

  function handlePublishAll() {
    if (!canPublishAll) return;

    const assessments = filteredReviews.map((review) => ({
      session_id: review.sessionId,
      student_id: review.studentId,
    }));
    releaseAllResults({ assessments });
  }

  return (
    <main className="ml-64 min-h-screen px-12 pb-12 pt-24">
      <div className="mb-8">
        <NavLink
          className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-on-surface-variant transition-colors hover:text-primary"
          to="/home"
        >
          <span
            className="material-symbols-outlined text-sm"
            style={{ verticalAlign: "middle" }}
            data-icon="arrow_back"
          >
            arrow_back
          </span>
          BACK TO COURSES
        </NavLink>
        <h1 className="mt-4 font-headline text-4xl font-extrabold tracking-tight text-on-surface">
          Review Submissions
        </h1>
      </div>

      <div className="overflow-hidden rounded-xl bg-surface-container-lowest shadow-[0_4px_24px_rgba(43,52,55,0.04)]">
        <div className="flex flex-col justify-between gap-4 bg-surface-container-low/30 p-6 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <button
              className="headline-font flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 font-headline text-sm font-semibold text-on-primary transition-all hover:bg-primary-dim disabled:opacity-50"
              onClick={handlePublishAll}
              disabled={!canPublishAll}
            >
              <span
                className="material-symbols-outlined text-lg"
                style={{
                  verticalAlign: "middle",
                  fontVariationSettings: '"FILL" 1',
                }}
                data-icon="publish"
                data-weight="fill"
              >
                publish
              </span>
              Publish All
            </button>

            <button
              className="flex items-center gap-2 rounded-xl border-2 border-tertiary/40 bg-tertiary-container/40 px-6 py-2.5 font-headline text-sm font-semibold text-on-tertiary-container transition-all hover:bg-tertiary-container disabled:opacity-50"
              onClick={handleAcceptAllAi}
              disabled={!canAcceptAllAi || isApprovingAll}
            >
              <span
                className="material-symbols-outlined text-lg"
                style={{
                  verticalAlign: "middle",
                  fontVariationSettings: '"FILL" 1',
                }}
              >
                auto_awesome
              </span>
              Accept All AI
            </button>

            <div className="text-sm font-medium text-on-surface-variant">
              Showing{" "}
              <span className="text-on-surface">{filteredReviews.length}</span>{" "}
              submissions
            </div>
          </div>

          <div className="relative w-full md:w-80">
            <span
              className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-outline-variant"
              style={{ verticalAlign: "middle" }}
              data-icon="filter_list"
            >
              filter_list
            </span>
            <input
              className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 pl-10 pr-4 text-sm outline-none transition-all focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
              placeholder="Filter by student or course..."
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
          </div>
        </div>

        <PendingStudentTable
          filteredReviews={filteredReviews}
          grades={grades}
          onGradeChange={handleGradeChange}
          isValidGrade={isValidGrade}
        />
      </div>
    </main>
  );
}

export default InstructorPendingGrades;
