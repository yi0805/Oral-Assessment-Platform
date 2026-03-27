import LoginButton from "../features/authentication/LoginButton";

function Login() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden p-6 sm:p-12">
      <div className="pointer-events-none absolute left-0 top-0 z-0 h-full w-full">
        <div className="absolute right-[-10%] top-[-10%] h-[500px] w-[500px] rounded-full bg-primary-container/20 blur-[120px]"></div>
        <div className="absolute bottom-[-5%] left-[-5%] h-[400px] w-[400px] rounded-full bg-tertiary-container/30 blur-[100px]"></div>
      </div>

      <main className="relative z-10 flex w-full max-w-5xl flex-col items-center">
        <header className="mb-16 text-center">
          <div className="mb-4 flex items-center justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/10">
              <img
                src="/WhereRU.png"
                alt="WhereRU logo"
                className="h-8 w-8 object-contain"
              />
            </div>
          </div>
          <h1 className="headline-font text-glow text-4xl font-extrabold tracking-tight text-primary">
            WhereRU
          </h1>
          <p className="mt-2 text-[10px] font-medium uppercase tracking-wide text-on-surface-variant opacity-70">
            Advanced Oral Assessment Platform
          </p>
        </header>
      </main>

      <div className="grid w-full max-w-4xl grid-cols-1 gap-8 md:grid-cols-2">
        <LoginButton role="student" />
        <LoginButton role="instructor" />
      </div>

      <footer class="mt-20 flex flex-col items-center gap-4 text-center">
        <div class="flex gap-8 text-sm font-medium text-on-surface-variant">
          <a class="transition-colors hover:text-primary" href="#">
            Help Center
          </a>
          <a class="transition-colors hover:text-primary" href="#">
            Privacy Policy
          </a>
          <a class="transition-colors hover:text-primary" href="#">
            Accessibility
          </a>
        </div>
        <p class="font-body text-xs text-outline">
          © 2026 WhereRU. All rights reserved.
        </p>
      </footer>

      <div className="fixed bottom-8 right-8 flex items-center gap-3 rounded-full border border-outline-variant/10 bg-surface-container-low px-4 py-2 shadow-sm">
        <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500"></div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Systems Operational
        </span>
      </div>
    </div>
  );
}

export default Login;

//  <StandaloneLayout>
//       <BaseCard $variant="login">
//         <LoginChooser />
//       </BaseCard>
//     </StandaloneLayout>
