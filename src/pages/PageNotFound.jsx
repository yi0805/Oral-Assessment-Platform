import { NavLink } from "react-router";

function PageNotFound() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden p-6 sm:p-12">
      <div className="pointer-events-none absolute left-0 top-0 z-0 h-full w-full">
        <div className="absolute right-[-10%] top-[-10%] h-[500px] w-[500px] rounded-full bg-primary-container/20 blur-[120px]"></div>
        <div className="absolute bottom-[-5%] left-[-5%] h-[400px] w-[400px] rounded-full bg-tertiary-container/30 blur-[100px]"></div>
      </div>

      <main className="relative z-10 flex w-full max-w-2xl flex-col items-center text-center">
        <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/10">
          <img
            src="/WhereRU.png"
            alt="WhereRU logo"
            className="h-8 w-8 object-contain"
          />
        </div>

        <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant opacity-70">
          Error Code
        </p>
        <h1 className="headline-font text-glow mt-2 text-[120px] font-extrabold leading-none tracking-tight text-primary sm:text-[160px]">
          404
        </h1>

        <h2 className="mt-6 font-headline text-2xl font-extrabold tracking-tight text-on-surface sm:text-3xl">
          The page you&apos;re looking for doesn&apos;t exist.
        </h2>

        <NavLink
          to="/home"
          className="group mt-10 inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]"
        >
          <span
            className="material-symbols-outlined text-base transition-transform group-hover:-translate-x-1"
            data-icon="arrow_back"
          >
            arrow_back
          </span>
          <span>Back to Home</span>
        </NavLink>
      </main>

      <div className="fixed bottom-8 right-8 flex items-center gap-3 rounded-full border border-outline-variant/10 bg-surface-container-low px-4 py-2 shadow-sm">
        <div className="h-2 w-2 animate-pulse rounded-full bg-amber-500"></div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Off the Map
        </span>
      </div>
    </div>
  );
}

export default PageNotFound;
