
function ScoreReview() {

  return (
    <>
    <main class="min-h-screen pl-64 pt-16">
      <div class="mx-auto max-w-6xl px-12 py-16">
        {/* <!-- Academic Breadcrumb / Header --> */}
        <div class="mb-12">
          <span
            class="mb-2 block text-[11px] font-bold uppercase tracking-[0.2em] text-outline-variant"
            >History of Philosophy / Oral Examination</span
          >
          <div class="flex items-end justify-between">
            <h1
              class="font-headline text-4xl font-extrabold tracking-tight text-on-surface"
            >
              Student Response Detail
            </h1>
            <div class="flex gap-3">
              <button
                class="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
              >
                Previous
              </button>
              <button
                class="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
              >
                Next Student
              </button>
            </div>
          </div>
        </div>
        {/* <!-- Focus Container: Bento Grid Layout --> */}
        <div class="grid grid-cols-12 gap-8">
          {/* <!-- Student Profile & Score (Column 1-4) --> */}
          <div class="col-span-12 flex flex-col gap-8 lg:col-span-4">
            {/* <!-- Student Identity Card --> */}
            <div
              class="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8"
            >
              <div class="flex flex-col items-center text-center">
                <div
                  class="mb-4 h-24 w-24 rounded-full border-2 border-primary-container p-1"
                >
                  <img
                    alt="Student avatar"
                    class="h-full w-full rounded-full object-cover"
                    data-alt="close-up portrait of a young male university student with a thoughtful expression and soft natural lighting"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYuZmk-CbqdAOi1wZcjVE5z9s7ISH4vGRk8NXikuHzkrpemW3Jt0zIHT8yToMcOlgUs9c3iMgrGzl52rr60yhdLAgJC9keR1SytRGyFnh6UAx5wGzxt354whQBEE7hO327TMifBRnkML-4K--9UDPnOB9maUhZn2y9jERfH5xCTKcNngbeFihS_YnNH8hkIgxUJB79qXZze8LGCHGIk6qVxpM0D0WD7C6AfeZ_2VlVmsg4xEsJqAeGbxKUo5Mvv_js5dr4yWIbc6Nz"
                  />
                </div>
                <h2 class="font-headline text-xl font-bold text-on-surface">
                  Julian Thorne
                </h2>
                <p class="mb-4 text-sm text-outline">
                  Philosophy Major, Junior Year
                </p>
                <div class="flex gap-2">
                  <span
                    class="rounded-full bg-surface-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant"
                    >Term 2</span
                  >
                  <span
                    class="rounded-full bg-tertiary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-tertiary-container"
                    >Active Enrollment</span
                  >
                </div>
              </div>
            </div>
            {/* <!-- Preliminary AI Score (Highlighted) --> */}
            <div
              class="rounded-xl border border-primary/10 bg-primary-container p-8"
            >
              <div class="mb-2 flex items-start justify-between">
                <span
                  class="text-[11px] font-bold uppercase tracking-widest text-on-primary-container"
                  >AI Preliminary Score</span
                >
                <span
                  class="material-symbols-outlined text-on-primary-container opacity-50"
                  >auto_awesome</span
                >
              </div>
              <div class="flex items-baseline gap-1">
                <span
                  class="font-headline text-5xl font-extrabold tracking-tighter text-on-primary-container"
                  >88</span
                >
                <span
                  class="text-lg font-bold text-on-primary-container opacity-60"
                  >/100</span
                >
              </div>
              <p
                class="mt-4 text-xs font-medium leading-snug text-on-primary-container"
              >
                Confidence: High. The AI detected strong conceptual alignment
                with key texts but noted a slight hesitation in the oral
                transcript.
              </p>
            </div>
            {/* <!-- AI Summary Bento Box --> */}
            <div class="rounded-xl bg-surface-container-high p-8">
              <div class="mb-4 flex items-center gap-3">
                <span class="material-symbols-outlined text-primary"
                  >analytics</span
                >
                <h3 class="font-headline font-bold text-on-surface">
                  AI Summary
                </h3>
              </div>
              <div class="space-y-6">
                <div>
                  <span
                    class="mb-2 block text-[10px] font-bold uppercase tracking-wider text-outline"
                    >Key Concepts</span
                  >
                  <div class="flex flex-wrap gap-2">
                    <span
                      class="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >The Divided Line</span
                    >
                    <span
                      class="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Form of the Good</span
                    >
                    <span
                      class="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Eikasia</span
                    >
                    <span
                      class="rounded-md border border-outline-variant/20 bg-white px-2 py-1 text-[11px] font-medium"
                      >Dialectic</span
                    >
                  </div>
                </div>
                <div>
                  <span
                    class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-outline"
                    >Sentiment &amp; Confidence</span
                  >
                  <div class="mb-3 h-1.5 w-full rounded-full bg-white">
                    <div
                      class="h-1.5 rounded-full bg-primary"
                      style="width: 92%"
                    ></div>
                  </div>
                  <p class="text-xs leading-relaxed text-on-surface-variant">
                    Response shows high lexical diversity and conceptual
                    accuracy.
                  </p>
                </div>
              </div>
            </div>
          </div>
          {/* <!-- Q&A Content Section (Column 5-12) --> */}
          <div class="col-span-12 flex flex-col gap-6 lg:col-span-8">
            {/* <!-- Pagination Controls --> */}
            <div
              class="flex items-center justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest px-6 py-4 shadow-sm"
            >
              <div class="flex items-center gap-4">
                <button
                  class="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim disabled:cursor-not-allowed disabled:opacity-30"
                  disabled=""
                >
                  <span class="material-symbols-outlined text-base"
                    >chevron_left</span
                  >
                  PREVIOUS
                </button>
                <span class="h-4 w-[1px] bg-outline-variant/30"></span>
                <button
                  class="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim"
                >
                  NEXT
                  <span class="material-symbols-outlined text-base"
                    >chevron_right</span
                  >
                </button>
              </div>
              <span
                class="text-[11px] font-bold uppercase tracking-widest text-outline"
                >Question 1 of 4</span
              >
            </div>
            {/* <!-- Single Question Display --> */}
            <div class="space-y-6">
              <div class="group">
                {/* <!-- Question Header --> */}
                <div class="mb-6 flex items-start gap-4">
                  <span
                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container font-headline font-bold text-primary"
                    >1</span
                  >
                  <div class="pt-1.5">
                    <h3
                      class="mb-2 font-headline text-[11px] font-bold uppercase tracking-widest text-on-surface-variant"
                    >
                      Core Theory Assessment
                    </h3>
                    <p
                      class="font-body text-lg font-medium leading-relaxed text-on-surface"
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
                  class="ml-14 overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm"
                >
                  {/* <!-- Transcript Header --> */}
                  <div
                    class="flex items-center justify-between border-b border-outline-variant/10 bg-surface-container-low px-8 py-4"
                  >
                    <div class="flex items-center gap-2">
                      <span
                        class="material-symbols-outlined text-sm text-secondary"
                        >subject</span
                      >
                      <span
                        class="text-[11px] font-bold uppercase tracking-widest text-outline"
                        >Student Response Transcript</span
                      >
                    </div>
                  </div>
                  {/* <!-- Transcript Text (Simplified: No Timestamps) --> */}
                  <div class="space-y-6 p-8">
                    <p class="text-sm leading-relaxed text-on-surface">
                      "Right, so the Cave Allegory... it's really about the
                      transition from ignorance to enlightenment. The shadows on
                      the wall represent the sensory world—the *eikasia*—where
                      we only see reflections of reality."
                    </p>
                    <p class="text-sm leading-relaxed text-on-surface">
                      "When the prisoner is dragged out, the sunlight is painful
                      at first. This is crucial because it shows that education
                      isn't just downloading data; it's a painful reorientation
                      of the whole soul. The sun itself is the Form of the
                      Good."
                    </p>
                    <p class="text-sm leading-relaxed text-on-surface">
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
              class="mt-4 rounded-xl border-2 border-primary/20 bg-surface-container-lowest p-8 shadow-xl"
            >
              <h3 class="mb-6 font-headline text-xl font-bold text-on-surface">
                Instructor Review
              </h3>
              <div class="grid grid-cols-1 gap-8 md:grid-cols-3">
                <div class="space-y-4 md:col-span-2">
                  <label
                    class="text-xs font-bold uppercase tracking-widest text-outline"
                    >Final Assessment Comments</label
                  >
                  <textarea
                    class="h-32 w-full rounded-xl border-outline-variant/30 bg-surface-container-low p-4 font-body text-sm placeholder:text-outline/50 focus:border-primary focus:ring-0"
                    placeholder="Provide qualitative feedback for Julian..."
                  ></textarea>
                </div>
                <div class="flex flex-col gap-6">
                  <div>
                    <label
                      class="mb-2 block text-xs font-bold uppercase tracking-widest text-outline"
                      >Override Score</label
                    >
                    <div class="flex items-center gap-3">
                      <input
                        class="w-24 border-b-2 border-primary bg-transparent font-headline text-3xl font-extrabold text-primary focus:outline-none"
                        type="number"
                        value="88"
                      />
                      <span class="text-lg font-bold text-outline">/ 100</span>
                    </div>
                  </div>
                  <div class="space-y-3">
                    <button
                      class="w-full rounded-xl bg-primary py-4 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]"
                    >
                      Confirm &amp; Submit Grade
                    </button>
                    <button
                      class="w-full rounded-xl bg-surface-container py-3 text-sm font-bold text-on-surface-variant transition-all hover:bg-surface-container-high"
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
        <div class="h-16"></div>
      </div>
    </main>
    </>
  );
}