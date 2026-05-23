function Spinner() {
  return (
    <div className="flex min-h-screen">
      <main className="flex flex-1 items-center justify-center bg-surface p-8 pt-16">
        <div className="flex w-full max-w-md flex-col items-center text-center">
          <div className="relative mb-12 flex items-center justify-center">
            <div className="absolute h-28 w-28 rounded-full border-[3px] border-surface-container-highest"></div>

            <div className="animate-spin-slow absolute h-28 w-28 rounded-full border-[3px] border-b-transparent border-l-transparent border-r-transparent border-t-primary"></div>

            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
              <span
                className="material-symbols-outlined text-2xl text-primary"
                style={{ fontVariationSettings: '"FILL" 1' }}
              >
                auto_stories
              </span>
            </div>
          </div>
          <div className="space-y-4">
            <h1 className="font-headline text-2xl font-bold tracking-tight text-on-surface">
              Loading your data...
            </h1>
          </div>

          <div className="mt-16 grid w-full max-w-sm grid-cols-2 gap-4">
            <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-4">
              <span
                className="material-symbols-outlined text-lg text-primary"
                style={{ fontVariationSettings: '"FILL" 1' }}
              >
                check_circle
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                Archives Linked
              </span>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-4">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-surface-container-highest border-t-primary"></div>
              <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                Processing...
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Spinner;
