import { useLocation, NavLink } from "react-router";

export default function InstructorDashboard() {
  const { state } = useLocation();
  const course = state?.course || [];

  console.log(course);

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            {/* <a
              className="group mb-4 flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-outline-variant transition-colors hover:text-primary"
              href="#"
            >
              <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
                arrow_back
              </span>
              Back to Courses
            </a> */}
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
            <span className="mb-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline">
              {course.id}
            </span>
            <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
              Assessment Dashboard
            </h1>
          </div>
          <div className="relative min-w-[320px]">
            <label className="mb-1.5 ml-1 block text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
              Select Assessment
            </label>
            <div className="group flex cursor-pointer items-center justify-between rounded-xl border border-outline-variant/20 bg-surface-container-lowest px-4 py-3 transition-colors hover:bg-surface-bright">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary">
                  description
                </span>
                <span className="text-sm font-semibold text-on-surface">
                  Mid-Term: Neural Network Architectures
                </span>
              </div>
              <span className="material-symbols-outlined text-outline transition-colors group-hover:text-primary">
                expand_more
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
