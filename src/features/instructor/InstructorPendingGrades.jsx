import { NavLink } from "react-router";

function InstructorPendingGrades() {
  return (
    <main className="ml-64 min-h-screen px-12 pb-12 pt-24">
      <div className="mb-8">
        <NavLink
          className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-on-surface-variant transition-colors hover:text-primary"
          to="/home"
        >
          <span
            className="material-symbols-outlined text-sm"
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
            <button className="flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 font-headline text-sm font-semibold text-on-primary transition-all hover:bg-primary-dim">
              <span
                className="material-symbols-outlined text-lg"
                data-icon="publish"
                data-weight="fill"
                style={{ fontVariationSettings: '"FILL" 1' }}
              >
                publish
              </span>
              Publish All
            </button>
            <div className="text-sm font-medium text-on-surface-variant">
              Showing <span className="text-on-surface">24</span> submissions
            </div>
          </div>
          <div className="relative w-full md:w-80">
            <span
              className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-outline-variant"
              data-icon="filter_list"
            >
              filter_list
            </span>
            <input
              className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 pl-10 pr-4 text-sm outline-none transition-all focus:border-primary/40 focus:ring-2 focus:ring-primary/20"
              placeholder="Filter by student or course..."
              type="text"
            />
          </div>
        </div>
      </div>
    </main>
  );
}

export default InstructorPendingGrades;
