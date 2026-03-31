import { useEffect } from "react";
import { NavLink } from "react-router";

import { useMoveBack } from "../../hooks/useMoveBack";

function Transcipt() {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const moveback = useMoveBack();

  return (
    <div className="font-body">
      <main className="min-h-screen pl-64 pt-16">
        <div className="mx-auto max-w-6xl px-12 py-16">
          <button
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
            onClick={moveback}
          >
            <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>
            <span className="font-body uppercase tracking-widest">
              Back to Dashboard
            </span>
          </button>
          <div className="mb-12">
            <div className="flex items-end justify-between">
              <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
                Student Response Detail
              </h1>

              <div className="flex gap-3">
                <button className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container">
                  Previous
                </button>
                <button className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container">
                  Next Student
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 flex flex-col gap-8 lg:col-span-4">
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8">
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 h-24 w-24 rounded-full border-2 border-primary-container p-1">
                    <img
                      alt="Student avatar"
                      className="h-full w-full rounded-full object-cover"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYuZmk-CbqdAOi1wZcjVE5z9s7ISH4vGRk8NXikuHzkrpemW3Jt0zIHT8yToMcOlgUs9c3iMgrGzl52rr60yhdLAgJC9keR1SytRGyFnh6UAx5wGzxt354whQBEE7hO327TMifBRnkML-4K--9UDPnOB9maUhZn2y9jERfH5xCTKcNngbeFihS_YnNH8hkIgxUJB79qXZze8LGCHGIk6qVxpM0D0WD7C6AfeZ_2VlVmsg4xEsJqAeGbxKUo5Mvv_js5dr4yWIbc6Nz"
                    />
                  </div>
                  <h2 className="font-headline text-xl font-bold text-on-surface">
                    XXXXXX
                  </h2>
                  <p className="mb-4 text-sm text-outline">XXXXX</p>

                  <div className="flex gap-2">
                    <span className="rounded-full bg-tertiary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-tertiary-container">
                      Active Enrollment
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-primary/10 bg-primary-container p-8">
                <div className="mb-2 flex items-start justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-widest text-on-primary-container">
                    Score
                  </span>
                  <span className="material-symbols-outlined text-on-primary-container opacity-50">
                    auto_awesome
                  </span>
                </div>

                <div className="flex items-baseline gap-1">
                  <span className="font-headline text-5xl font-extrabold tracking-tighter text-on-primary-container">
                    xxxx
                  </span>
                  <span className="text-lg font-bold text-on-primary-container opacity-60">
                    /xxxxx
                  </span>
                </div>
                <p className="mt-4 text-xs font-medium leading-snug text-on-primary-container">
                  xxxxxxxxxxxx
                </p>
              </div>
            </div>

            <div className="col-span-12 flex flex-col gap-6 lg:col-span-8">
              <div className="flex items-center justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest px-6 py-4 shadow-sm">
                <div className="flex items-center gap-4">
                  <button
                    className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim disabled:cursor-not-allowed disabled:opacity-30"
                    disabled=""
                  >
                    <span className="material-symbols-outlined text-base">
                      chevron_left
                    </span>
                    PREVIOUS
                  </button>
                  <span className="h-4 w-[1px] bg-outline-variant/30"></span>
                  <button className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim">
                    NEXT
                    <span className="material-symbols-outlined text-base">
                      chevron_right
                    </span>
                  </button>
                </div>

                <span className="text-[11px] font-bold uppercase tracking-widest text-outline">
                  Question xxx of xxxx
                </span>
              </div>

              <div className="space-y-6">
                <div className="group">
                  <div className="mb-6 flex items-start gap-4">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container font-headline font-bold text-primary">
                      xxxxxx
                    </span>

                    <div className="pt-1.5">
                      <h3 className="mb-2 font-headline text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                        xxxxxxxx
                      </h3>
                      <p className="font-body text-lg font-medium leading-relaxed text-on-surface">
                        xxxxxxxxxxxxxxxxxxx
                      </p>
                    </div>
                  </div>

                  <div className="ml-14 overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm">
                    <div className="flex items-center justify-between border-b border-outline-variant/10 bg-surface-container-low px-8 py-4">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-secondary">
                          subject
                        </span>
                        <span className="text-[11px] font-bold uppercase tracking-widest text-outline">
                          Student Response Transcript
                        </span>
                      </div>
                    </div>

                    <div className="space-y-6 p-8">
                      <p className="text-sm leading-relaxed text-on-surface">
                        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-xl border-2 border-primary/20 bg-surface-container-lowest p-8 shadow-xl">
                <h3 className="mb-6 font-headline text-xl font-bold text-on-surface">
                  Instructor Review
                </h3>
                <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                  <div className="space-y-4 md:col-span-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-outline">
                      Final Assessment Comments
                    </label>
                    <textarea
                      className="h-32 w-full rounded-xl border-outline-variant/30 bg-surface-container-low p-4 font-body text-sm placeholder:text-outline/50 focus:border-primary focus:ring-0"
                      placeholder="Provide qualitative feedback..."
                    ></textarea>
                  </div>

                  <div className="flex flex-col gap-6">
                    <div>
                      <label className="mb-2 block text-xs font-bold uppercase tracking-widest text-outline">
                        Final Score
                      </label>

                      <div className="flex items-center gap-3">
                        <input
                          className="w-24 border-b-2 border-primary bg-transparent font-headline text-3xl font-extrabold text-primary focus:outline-none"
                          type="number"
                        />

                        <span className="text-lg font-bold text-outline">
                          / xxxxx
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <button className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]">
                        Confirm &amp; Submit Grade
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="h-16"></div>
        </div>
      </main>
    </div>
  );
}

export default Transcipt;
