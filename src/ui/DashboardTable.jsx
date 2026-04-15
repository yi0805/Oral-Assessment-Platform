import { useState } from "react";
import { useNavigate } from "react-router";

import { useGrading } from "../features/instructor/useGrading";
import { useReleaseResult } from "../features/instructor/useReleaseResult";
import { useApproveAiGrade } from "../features/instructor/useApproveAiGrade";

function DashboardTable({
  filteredStudents,
  isValidGrade,
  grades,
  onGradeChange,
}) {
  const navigate = useNavigate();

  const [currentPage, setCurrentPage] = useState(1);

  const { updateGrade } = useGrading();
  const { releaseResult } = useReleaseResult();
  const { approveAiGrade, isPending: isApproving } = useApproveAiGrade();

  const rowsPerPage = 6;
  const totalPages = Math.ceil(filteredStudents.length / rowsPerPage);

  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentRows = filteredStudents.slice(startIndex, endIndex);

  function goToPage(page) {
    setCurrentPage(page);
  }

  function goToPrevPage() {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  }

  function goToNextPage() {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  }

  function handleViewAnswer(student) {
    const reviews = filteredStudents.map((item) => ({
      sessionId: item.session_id,
    }));
    const currentReviewIndex = filteredStudents.findIndex(
      (item) => item.session_id === student.session_id,
    );

    navigate(`/instructor/transcript/${student.session_id}`, {
      state: { reviews, currentReviewIndex },
    });
  }

  function handleGradeChange(sessionId, grade) {
    if (!isValidGrade(grade)) return;

    updateGrade({ sessionId, grade: Number(grade) });
  }

  function handleRelease(sessionId, studentId) {
    releaseResult({ sessionId, studentId });
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-surface-container-low">
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                Publish
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                Student
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                AI Score
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                AI Summary
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                Final Score
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                Status
              </th>
              <th className="px-8 py-4 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-outline-variant">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-surface-container">
            {currentRows.length > 0 ? (
              currentRows.map((student) => {
                const currentGrade = grades[student.session_id] ?? "";
                const canPublish = isValidGrade(currentGrade);

                const isPublished = student.status === "published";
                const isReview = student.status === "review";
                const isInProgress = student.status === "inprogress";
                return (
                  <tr
                    className="group transition-colors hover:bg-surface-container-high/30"
                    key={student.session_id}
                  >
                    <td className="px-8 py-5">
                      {isPublished && (
                        <label className="relative inline-flex cursor-pointer items-center">
                          <input
                            className="peer sr-only"
                            type="checkbox"
                            checked={true}
                            disabled={true}
                          />

                          <div className="peer h-5 w-10 rounded-full bg-surface-container-highest after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none"></div>
                        </label>
                      )}

                      {isReview && (
                        <label className="relative inline-flex cursor-pointer items-center">
                          <input
                            className="peer sr-only"
                            type="checkbox"
                            disabled={!canPublish}
                            onChange={() => {
                              handleRelease(
                                student.session_id,
                                student.student_id,
                              );
                            }}
                          />

                          <div className="peer h-5 w-10 rounded-full bg-surface-container-highest after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none"></div>
                        </label>
                      )}

                      {isInProgress && (
                        <span className="text-sm font-bold text-outline-variant">
                          —
                        </span>
                      )}
                    </td>

                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                        <img
                          alt="Student Avatar"
                          className="h-10 w-10 rounded-full object-cover"
                          src={student.student_image || "/WhereRU.png"}
                        />

                        <div>
                          <p className="text-sm font-bold text-on-surface">
                            {student.student_name || "Unknown Student"}
                          </p>

                          <p className="text-[10px] text-on-surface-variant">
                            {student.student_email || "No email available"}
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2">
                        <span className="font-headline text-sm font-bold text-tertiary">
                          {student.ai_suggested_score ?? "-"}/100
                        </span>

                        <span className="material-symbols-outlined text-[16px] text-outline">
                          auto_awesome
                        </span>
                      </div>
                    </td>

                    <td className="max-w-xs px-8 py-5">
                      <p className="line-clamp-2 text-xs italic text-on-surface-variant">
                        {student.ai_summary || "No summary available."}
                      </p>
                    </td>

                    <td className="px-8 py-5">
                      {isPublished && (
                        <span className="inline-flex min-w-[3rem] items-center justify-center rounded-lg bg-surface-container px-3 py-1.5 text-sm font-bold text-on-surface shadow-sm">
                          {student.final_grade ?? "-"}
                        </span>
                      )}

                      {isReview && (
                        <input
                          className="h-9 w-12 rounded-lg border border-outline-variant/30 bg-white text-center text-sm font-semibold outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={currentGrade}
                          onChange={(e) => {
                            const val = e.target.value;

                            if (val === "" || /^\d+$/.test(val)) {
                              onGradeChange(student.session_id, val);
                            }
                          }}
                          onBlur={(e) => {
                            const raw = e.target.value;

                            if (raw === "") {
                              handleGradeChange(student.session_id, "");
                              return;
                            }

                            const val = Math.min(
                              100,
                              Math.max(0, parseInt(raw, 10) || 0),
                            );

                            handleGradeChange(student.session_id, val);
                          }}
                        />
                      )}

                      {isInProgress && (
                        <span className="text-sm font-bold text-outline-variant">
                          —
                        </span>
                      )}
                    </td>

                    <td className="px-8 py-5">
                      {isPublished && (
                        <span className="rounded-full bg-primary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-primary-container">
                          Published
                        </span>
                      )}

                      {isReview && (
                        <span className="rounded-full bg-error-container/20 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-error">
                          Review
                        </span>
                      )}

                      {isInProgress && (
                        <span className="rounded-full border border-outline-variant/40 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                          In Progress
                        </span>
                      )}
                    </td>

                    <td className="px-8 py-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {isReview && (
                          <button
                            className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-tertiary/30 bg-tertiary-container/40 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-on-tertiary-container transition-all hover:bg-tertiary-container disabled:cursor-not-allowed disabled:opacity-40"
                            onClick={() =>
                              approveAiGrade({ sessionId: student.session_id })
                            }
                            disabled={
                              isApproving || !student.ai_suggested_score
                            }
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
                        )}

                        {!isInProgress && (
                          <button
                            className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-outline-variant/30 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-surface-container"
                            onClick={() => handleViewAnswer(student)}
                          >
                            <span className="material-symbols-outlined text-sm">
                              visibility
                            </span>
                            View Answer
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
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
            )}
          </tbody>
        </table>
      </div>

      {filteredStudents.length > 0 && (
        <div className="flex items-center justify-between border-t border-surface-container bg-surface-container-low px-8 py-4">
          <span className="text-xs font-medium text-on-surface-variant">
            Showing {startIndex + 1}-
            {Math.min(endIndex, filteredStudents.length)} of{" "}
            {filteredStudents.length} submissions
          </span>

          <div className="flex gap-2">
            <button
              className="rounded p-2 text-outline transition-colors hover:bg-surface-container"
              onClick={goToPrevPage}
              disabled={currentPage === 1}
            >
              <span className="material-symbols-outlined text-sm">
                chevron_left
              </span>
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                className={`rounded p-2 px-4 text-sm font-bold transition-colors hover:bg-surface-container ${currentPage === page ? "text-on-surface" : "text-outline"}`}
                key={page}
                onClick={() => goToPage(page)}
              >
                {page}
              </button>
            ))}

            <button
              className="rounded p-2 text-outline transition-colors hover:bg-surface-container"
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
            >
              <span className="material-symbols-outlined text-sm">
                chevron_right
              </span>
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default DashboardTable;
