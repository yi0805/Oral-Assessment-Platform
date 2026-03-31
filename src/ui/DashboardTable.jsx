import { useState } from "react";
import { useNavigate } from "react-router";

function DashboardTable({ selectedAssessmentResults }) {
  const navigate = useNavigate();

  const rowsPerPage = 6;
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(selectedAssessmentResults.length / rowsPerPage);

  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentRows = selectedAssessmentResults.slice(startIndex, endIndex);

  function goToPage(page) {
    setCurrentPage(page);
  }

  function goToPrevPage() {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  }

  function goToNextPage() {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
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
              currentRows.map((assessment, index) => (
                <tr
                  className="group transition-colors hover:bg-surface-container-high/30"
                  key={index}
                >
                  <td className="px-8 py-5">
                    {/* change later */}
                    {assessment ? (
                      <div className="flex items-center justify-center gap-1 text-emerald-600">
                        <span className="material-symbols-outlined text-sm">
                          check_circle
                        </span>
                        <span className="text-[10px] font-bold uppercase tracking-wider">
                          Published
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center">
                        <button className="rounded-lg border border-primary/30 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-primary transition-all duration-200 hover:bg-primary hover:text-white"></button>
                      </div>
                    )}
                  </td>

                  <td className="px-8 py-5">
                    <div className="flex items-center gap-3">
                      <img
                        alt="Student Avatar"
                        className="h-10 w-10 rounded-full object-cover"
                        src="https://i.pravatar.cc/300?img=12"
                      />
                      <div>
                        <p className="text-sm font-bold text-on-surface">
                          {assessment.studentName}
                        </p>
                        <p className="text-[10px] text-on-surface-variant">
                          email
                        </p>
                      </div>
                    </div>
                  </td>

                  <td className="px-8 py-5">
                    <div className="flex items-center gap-2">
                      <span className="font-headline text-sm font-bold text-tertiary">
                        {parseInt(assessment.grade)}/10
                      </span>
                      <span className="material-symbols-outlined text-[16px] text-outline">
                        auto_awesome
                      </span>
                    </div>
                  </td>
                  <td className="max-w-xs px-8 py-5">
                    <p className="line-clamp-2 text-xs italic text-on-surface-variant">
                      AI summary
                    </p>
                  </td>
                  <td className="px-8 py-5">
                    <input
                      className="w-16 rounded-lg border-none bg-surface-container-low px-3 py-1 text-center text-sm font-bold text-on-surface focus:ring-1 focus:ring-primary"
                      type="text"
                    />
                  </td>
                  <td className="px-8 py-5">
                    <span
                      className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${assessment ? "bg-primary-container text-on-primary-container" : "bg-error-container/20 text-error"}`}
                    >
                      {assessment ? "Published" : "Unpublished"}
                    </span>
                  </td>
                  <td className="px-8 py-5 text-right">
                    <button
                      className="whitespace-now-content flex items-center gap-1.5 rounded-lg border border-outline-variant/30 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-surface-container"
                      onClick={() => {
                        navigate("/instructor/transcript");
                      }}
                    >
                      <span className="material-symbols-outlined text-sm">
                        visibility
                      </span>
                      View Answer
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan="7"
                  className="px-8 py-10 text-center text-sm text-on-surface-variant"
                >
                  No results found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {selectedAssessmentResults.length > 0 && (
        <div className="flex items-center justify-between border-t border-surface-container bg-surface-container-low px-8 py-4">
          <span className="text-xs font-medium text-on-surface-variant">
            Showing {currentRows.length} of xxx submissions
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
