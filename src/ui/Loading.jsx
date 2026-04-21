function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center font-body selection:bg-primary-container">
      <main className="flex w-full max-w-md flex-col items-center justify-center px-6 py-12 text-center">
        <div className="animate-subtle-pulse mb-16">
          <div className="flex flex-col items-center gap-3">
            <div className="mb-2 flex h-14 w-14 items-center justify-center rounded-xl bg-primary shadow-sm">
              <img
                src="/WhereRU.png"
                alt="WhereRU logo"
                className="h-8 w-8 object-contain"
              />
            </div>
            <h1 className="font-headline text-2xl font-extrabold uppercase tracking-tighter text-on-surface">
              WhereRU
            </h1>
            <p className="font-label text-xs font-medium uppercase tracking-widest text-on-surface-variant opacity-60">
              Oral Assessment
            </p>
          </div>
        </div>

        <div className="relative mb-12 flex items-center justify-center">
          <div className="absolute h-24 w-24 rounded-full border-[3px] border-surface-container-highest"></div>

          <div className="animate-spin-slow absolute h-24 w-24 rounded-full border-[3px] border-b-transparent border-l-transparent border-r-transparent border-t-primary"></div>

          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
            <span
              className="material-symbols-outlined text-xl text-primary"
              data-icon="verified_user"
              style={{ fontVariationSettings: '"FILL" 1' }}
            >
              verified_user
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="font-headline text-xl font-semibold tracking-tight text-on-surface">
            Securing your academic session...
          </h2>
          <p className="mx-auto max-w-xs font-body text-sm leading-relaxed text-on-surface-variant">
            We are calibrating your environment to ensure the highest standards
            of assessment integrity.
          </p>
        </div>

        <div className="mt-24 w-full border-t border-outline-variant/10 pt-8">
          <div className="flex items-center justify-center gap-8">
            <div className="flex flex-col items-center gap-1">
              <span className="font-label text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Encryption
              </span>
              <span className="font-body text-[10px] font-medium text-primary">
                AES-256 ACTIVE
              </span>
            </div>
            <div className="h-6 w-px bg-outline-variant/20"></div>
            <div className="flex flex-col items-center gap-1">
              <span className="font-label text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Instance
              </span>
              <span className="font-body text-[10px] font-medium text-primary">
                VIVA-CORE X
              </span>
            </div>
          </div>
        </div>
      </main>
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute right-[-10%] top-[-10%] h-[40%] w-[40%] rounded-full bg-primary-container/20 blur-[120px]"></div>
        <div className="absolute bottom-[-10%] left-[-10%] h-[40%] w-[40%] rounded-full bg-secondary-container/20 blur-[120px]"></div>
      </div>
    </div>
  );
}

export default Loading;
