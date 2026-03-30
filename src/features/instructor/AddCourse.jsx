
function AddCourse() {

  return (
    <>
    <main className="min-h-screen pl-64 pt-16">
      <div className="mx-auto max-w-6xl px-12 py-16">
        {/* <!-- Academic Breadcrumb / Header --> */}
        <div className="mb-12">
          <span
            className="mb-2 block text-[11px] font-bold uppercase tracking-[0.2em] text-outline-variant"
            >History of Philosophy / Oral Examination</span
          >
          <div className="flex items-end justify-between">
            <h1
              className="font-headline text-4xl font-extrabold tracking-tight text-on-surface"
            >
              Student Response Detail
            </h1>
            <div className="flex gap-3">
              <button
                className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
              >
                Previous
              </button>
              <button
                className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
              >
                Next Student
              </button>
            </div>
          </div>
        </div>
        {/* <!-- Focus Container: Bento Grid Layout --> */}
        <div className="grid grid-cols-12 gap-8">
          {/* <!-- Student Profile & Score (Column 1-4) --> */}
          <div className="col-span-12 flex flex-col gap-8 lg:col-span-4">
            {/* <!-- Student Identity Card --> */}
            <div
              className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8"
            >
              <div className="flex flex-col items-center text-center">
                <div
                  className="mb-4 h-24 w-24 rounded-full border-2 border-primary-container p-1"
                >
                  <img
                    alt="Student avatar"
                    className="h-full w-full rounded-full object-cover"
                    data-alt="close-up portrait of a young male university student with a thoughtful expression and soft natural lighting"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYuZmk-CbqdAOi1wZcjVE5z9s7ISH4vGRk8NXikuHzkrpemW3Jt0zIHT8yToMcOlgUs9c3iMgrGzl52rr60yhdLAgJC9keR1SytRGyFnh6UAx5wGzxt354whQBEE7hO327TMifBRnkML-4K--9UDPnOB9maUhZn2y9jERfH5xCTKcNngbeFihS_YnNH8hkIgxUJB79qXZze8LGCHGIk6qVxpM0D0WD7C6AfeZ_2VlVmsg4xEsJqAeGbxKUo5Mvv_js5dr4yWIbc6Nz"
                  />
                </div>
                <h2 className="font-headline text-xl font-bold text-on-surface">
                  Julian Thorne
                </h2>
                <p className="mb-4 text-sm text-outline">
                  Philosophy Major, Junior Year
                </p>
                <div className="flex gap-2">
                  <span
                    className="rounded-full bg-surface-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant"
                    >Term 2</span
                  >
                  <span
                    className="rounded-full bg-tertiary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-tertiary-container"
                    >Active Enrollment</span
                  >
                </div>
              </div>
            </div>
            {/* <!-- Preliminary AI Score (Highlighted) --> */}
            <div
              className="rounded-xl border border-primary/10 bg-primary-container p-8"
            >
              <div className="mb-2 flex items-start justify-between">
                <span
                  className="text-[11px] font-bold uppercase tracking-widest text-on-primary-container"
                  >AI Preliminary Score</span
                >
                <span
                  className="material-symbols-outlined text-on-primary-container opacity-50"
                  >auto_awesome</span
                >
              </div>
              <div className="flex items-baseline gap-1">
                <span
                  className="font-headline text-5xl font-extrabold tracking-tighter text-on-primary-container"
                  >88</span
                >
                <span
                  className="text-lg font-bold text-on-primary-container opacity-60"
                  >/100</span
                >
              </div>
              <p
                className="mt-4 text-xs font-medium leading-snug text-on-primary-container"
              >
                Confidence: High. The AI detected strong conceptual alignment
                with key texts but noted a slight hesitation in the oral
                transcript.
              </p>
            </div>
            {/* <!-- AI Summary Bento Box --> */}
            <div className="rounded-xl bg-surface-container-high p-8">
              <div className="mb-4 flex items-center gap-3">
                <span className="material-symbols-outlined text-primary"
                  >analytics</span
                >
                <h3 className="font-headline font-bold text-on-surface">
                  AI Summary
                </h3>
              </div>
              <div className="space-y-6">
                <div>
                  <span
                    className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-outline"
                    >Key Concepts</span
                  >
                  <div className="flex flex-wrap gap-2">
                    <span
                      className="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >The Divided Line</span
                    >
                    <span
                      className="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Form of the Good</span
                    >
                    <span
                      className="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Eikasia</span
                    >
                    <span
                      className="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Dialectic</span
                    >
                  </div>
                </div>
                <div>
                  <span
                    className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-outline"
                    >Sentiment &amp; Confidence</span
                  >
                  <div className="mb-3 h-1.5 w-full rounded-full bg-white">
                    <div
                      className="h-1.5 rounded-full bg-primary"
                      style={{ width: '92%' }}
                    ></div>
                  </div>
                  <p className="text-xs leading-relaxed text-on-surface-variant">
                    Response shows high lexical diversity and conceptual
                    accuracy.
                  </p>
                </div>
              </div>
            </div>
          </div>
          {/* <!-- Q&A Content Section (Column 5-12) --> */}
          <div className="col-span-12 flex flex-col gap-6 lg:col-span-8">
            {/* <!-- Pagination Controls --> */}
            <div
              className="flex items-center justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest px-6 py-4 shadow-sm"
            >
              <div className="flex items-center gap-4">
                <button
                  className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim disabled:cursor-not-allowed disabled:opacity-30"
                  disabled=""
                >
                  <span className="material-symbols-outlined text-base"
                    >chevron_left</span
                  >
                  PREVIOUS
                </button>
                <span className="h-4 w-[1px] bg-outline-variant/30"></span>
                <button
                  className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim"
                >
                  NEXT
                  <span className="material-symbols-outlined text-base"
                    >chevron_right</span
                  >
                </button>
              </div>
              <span
                className="text-[11px] font-bold uppercase tracking-widest text-outline"
                >Question 1 of 4</span
              >
            </div>
            {/* <!-- Single Question Display --> */}
            <div className="space-y-6">
              <div className="group">
                {/* <!-- Question Header --> */}
                <div className="mb-6 flex items-start gap-4">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container font-headline font-bold text-primary"
                    >1</span
                  >
                  <div className="pt-1.5">
                    <h3
                      className="mb-2 font-headline text-[11px] font-bold uppercase tracking-widest text-on-surface-variant"
                    >
                      Core Theory Assessment
                    </h3>
                    <p
                      className="font-body text-lg font-medium leading-relaxed text-on-surface"
                    >
                      "Explain the relationship between the Cave Allegory and
                      the theory of Forms in Plato's Republic. How does the
                      transition from shadows to sunlight represent the
                      epistemological journey?"
                    </p>
                  </div>
                </div>
                {/* <!-- Answer Content Container --> */}
                <div
                  className="ml-14 overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm"
                >
                  {/* <!-- Transcript Header --> */}
                  <div
                    className="flex items-center justify-between border-b border-outline-variant/10 bg-surface-container-low px-8 py-4"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="material-symbols-outlined text-sm text-secondary"
                        >subject</span
                      >
                      <span
                        className="text-[11px] font-bold uppercase tracking-widest text-outline"
                        >Student Response Transcript</span
                      >
                    </div>
                  </div>
                  {/* <!-- Transcript Text (Simplified: No Timestamps) --> */}
                  <div className="space-y-6 p-8">
                    <p className="text-sm leading-relaxed text-on-surface">
                      "Right, so the Cave Allegory... it's really about the
                      transition from ignorance to enlightenment. The shadows on
                      the wall represent the sensory world—the *eikasia*—where
                      we only see reflections of reality."
                    </p>
                    <p className="text-sm leading-relaxed text-on-surface">
                      "When the prisoner is dragged out, the sunlight is painful
                      at first. This is crucial because it shows that education
                      isn't just downloading data; it's a painful reorientation
                      of the whole soul. The sun itself is the Form of the
                      Good."
                    </p>
                    <p className="text-sm leading-relaxed text-on-surface">
                      "Uh, and then regarding the Theory of Forms... the journey
                      represents moving up the Divided Line. From belief to
                      dialectic reasoning. It's essentially Platonic dualism in
                      narrative form."
                    </p>
                  </div>
                </div>
              </div>
            </div>
            {/* <!-- Final Feedback & Override Section --> */}
            <div
              className="mt-4 rounded-xl border-2 border-primary/20 bg-surface-container-lowest p-8 shadow-xl"
            >
              <h3 className="mb-6 font-headline text-xl font-bold text-on-surface">
                Instructor Review
              </h3>
              <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                <div className="space-y-4 md:col-span-2">
                  <label
                    className="text-xs font-bold uppercase tracking-widest text-outline"
                    >Final Assessment Comments</label
                  >
                  <textarea
                    className="h-32 w-full rounded-xl border-outline-variant/30 bg-surface-container-low p-4 font-body text-sm placeholder:text-outline/50 focus:border-primary focus:ring-0"
                    placeholder="Provide qualitative feedback for Julian..."
                  ></textarea>
                </div>
                <div className="flex flex-col gap-6">
                  <div>
                    <label
                      className="mb-2 block text-xs font-bold uppercase tracking-widest text-outline"
                      >Override Score</label
                    >
                    <div className="flex items-center gap-3">
                      <input
                        className="w-24 border-b-2 border-primary bg-transparent font-headline text-3xl font-extrabold text-primary focus:outline-none"
                        type="number"
                        value="88"
                      />
                      <span className="text-lg font-bold text-outline">/ 100</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <button
                      className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]"
                    >
                      Confirm &amp; Submit Grade
                    </button>
                    <button
                      className="w-full rounded-xl bg-surface-container py-3 text-sm font-bold text-on-surface-variant transition-all hover:bg-surface-container-high"
                    >
                      Flag for Peer Review
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* <!-- Footer Spacing --> */}
        <div className="h-16"></div>
      </div>
    </main>
    </>
  );
}

export default AddCourse;