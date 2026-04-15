import { useState } from "react";
import { useNavigate } from "react-router";

import { useReleaseResult } from "../features/instructor/useReleaseResult";
import { useGrading } from "../features/instructor/useGrading.js";
import { useApproveAiGrade } from "../features/instructor/useApproveAiGrade";

function PendingStudentTable({
  filteredReviews = [],
  grades,
  onGradeChange,
  isValidGrade,
}) {
  const navigate = useNavigate();

  const [currentPage, setCurrentPage] = useState(1);

  const { updateGrade } = useGrading();
  const { releaseResult } = useReleaseResult();

  const { approveAiGrade, isPending: isApproving } = useApproveAiGrade();

  const rowsPerPage = 6;
  const totalPages = Math.ceil(filteredReviews.length / rowsPerPage);

  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentRows = filteredReviews.slice(startIndex, endIndex);

  function goToPage(page) {
    setCurrentPage(page);
  }

  function goToPrevPage() {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  }

  function goToNextPage() {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  }

  function handleReview(review) {
    const reviews = filteredReviews.map((item) => ({
      sessionId: item.sessionId,
    }));
    const currentReviewIndex = filteredReviews.findIndex(
      (item) => item.sessionId === review.sessionId,
    );

    navigate(`/instructor/transcript/${review.sessionId}`, {
      state: { reviews, currentReviewIndex },
    });
  }

  function handleRelease(sessionId, studentId) {
    releaseResult({ sessionId, studentId });
  }

  function handleGradeChange(sessionId, grade) {
    if (!isValidGrade(grade)) return;

    updateGrade({ sessionId, grade: Number(grade) });
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-outline-variant/10 bg-surface-container-low/50">
              <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Publish
              </th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Student
              </th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Course
              </th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Assessment Name
              </th>
              <th className="px-6 py-4 text-center text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                AI Score
              </th>
              <th className="px-6 py-4 text-center text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Final Score
              </th>
              <th className="px-6 py-4 text-right text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Action
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-outline-variant/5">
            {filteredReviews.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-6 py-10 text-center">
                  <div className="flex flex-col items-center justify-center gap-2 text-on-surface-variant">
                    <span className="material-symbols-outlined text-3xl opacity-60">
                      fact_check
                    </span>

                    <p className="text-sm font-medium">
                      Nothing to review right now
                    </p>

                    <p className="text-xs">
                      New submissions will appear here when they are ready for
                      grading.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              currentRows.map((review) => {
                const currentGrade = grades[review.sessionId] ?? "";
                const canPublish = isValidGrade(currentGrade);

                return (
                  <tr
                    className="group transition-colors hover:bg-surface-container-low/30"
                    key={review.sessionId}
                  >
                    <td className="px-6 py-5">
                      <label className="relative inline-flex cursor-pointer items-center">
                        <input
                          className="peer sr-only"
                          type="checkbox"
                          disabled={!canPublish}
                          onChange={() =>
                            handleRelease(review.sessionId, review.studentId)
                          }
                        />
                        <div className="peer h-5 w-10 rounded-full bg-surface-container-highest after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none"></div>
                      </label>
                    </td>

                    <td className="px-6 py-5">
                      <div className="flex items-center gap-3">
                        <img
                          className="h-10 w-10 rounded-full object-cover ring-2 ring-white"
                          data-alt="Close up of Elena Mitsotakis, a smiling female student with long brown hair in a bright outdoor campus setting"
                          src={review.image || "/WhereRU.png"}
                        />
                        <div>
                          <div className="headline-font text-sm font-bold text-on-surface">
                            {review.fullName || "Unknown Student"}
                          </div>
                          <div className="text-xs text-on-surface-variant">
                            {review.email || "No email provided"}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-5">
                      <span className="rounded-md bg-secondary-container px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-on-secondary-container">
                        {review.courseCode || "Unknown Course"}
                      </span>
                    </td>

                    <td className="px-6 py-5 text-sm font-medium text-on-surface-variant">
                      {review.title || "Unknown Assessment"}
                    </td>
                    <td className="px-6 py-5 text-center text-sm font-semibold text-on-surface">
                      {review.suggestedGrade || "-"}/100
                    </td>

                    <td className="px-6 py-5 text-center">
                      <input
                        className="h-9 w-12 rounded-lg border border-outline-variant/30 bg-white text-center text-sm font-semibold outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
                        type="number"
                        min={0}
                        max={100}
                        step={0.5}
                        value={currentGrade}
                        onChange={(e) => {
                          const val = e.target.value;

                          if (val === "" || /^\d+(\.\d?)?$/.test(val)) {
                            onGradeChange(review.sessionId, val);
                          }
                        }}
                        onBlur={(e) => {
                          const val = Math.min(
                            100,
                            Math.max(0, parseFloat(e.target.value) || 0),
                          );

                          handleGradeChange(review.sessionId, val);
                        }}
                      />
                    </td>

                    <td className="px-6 py-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          className="inline-flex items-center gap-1.5 rounded-lg border border-tertiary/30 bg-tertiary-container/40 px-3 py-2 text-xs font-bold uppercase tracking-wider text-on-tertiary-container transition-all hover:bg-tertiary-container disabled:cursor-not-allowed disabled:opacity-40"
                          onClick={() =>
                            approveAiGrade({ sessionId: review.sessionId })
                          }
                          disabled={isApproving || !review.suggestedGrade}
                          title="Accept AI suggested grade and release"
                        >
                          <span
                            className="material-symbols-outlined text-sm"
                            style={{ fontVariationSettings: '"FILL" 1' }}
                          >
                            auto_awesome
                          </span>
                          Accept AI
                        </button>

                        <button
                          className="rounded-lg border border-primary/20 px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary transition-all hover:bg-primary hover:text-white"
                          onClick={() => handleReview(review)}
                        >
                          Review
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {filteredReviews.length > 0 && (
        <div className="flex items-center justify-between border-t border-outline-variant/10 bg-surface-container-low/20 px-6 py-4">
          <span className="text-xs font-medium text-on-surface-variant">
            Page {currentPage} of {totalPages}
          </span>

          <nav className="flex items-center gap-1">
            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container-high"
              onClick={goToPrevPage}
              disabled={currentPage === 1}
            >
              <span
                className="material-symbols-outlined text-sm"
                style={{ verticalAlign: "middle" }}
                data-icon="chevron_left"
              >
                chevron_left
              </span>
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-medium transition-colors ${
                  currentPage === page
                    ? "bg-primary font-bold text-on-primary shadow-sm"
                    : "text-on-surface-variant hover:bg-surface-container-high"
                }`}
                key={page}
                onClick={() => goToPage(page)}
              >
                {page}
              </button>
            ))}

            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container-high"
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
            >
              <span
                className="material-symbols-outlined text-sm"
                style={{ verticalAlign: "middle" }}
                data-icon="chevron_right"
              >
                chevron_right
              </span>
            </button>
          </nav>
        </div>
      )}
    </>
  );
}

export default PendingStudentTable;
