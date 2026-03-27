import LoginChooser from "../features/authentication/LoginChooser";
import BaseCard from "../ui/BaseCard";
import StandaloneLayout from "../ui/StandaloneLayout";

function Login() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden p-6 sm:p-12">
      <div className="pointer-events-none absolute left-0 top-0 z-0 h-full w-full">
        <div className="absolute right-[-10%] top-[-10%] h-[500px] w-[500px] rounded-full bg-primary-container/20 blur-[120px]"></div>
        <div className="absolute bottom-[-5%] left-[-5%] h-[400px] w-[400px] rounded-full bg-tertiary-container/30 blur-[100px]"></div>
      </div>

      <h1 className="mb-4 text-sm font-bold uppercase tracking-widest text-yellow-500">
        Welcome Back!
      </h1>
      <StandaloneLayout>
        <BaseCard $variant="login">
          <LoginChooser />
        </BaseCard>
      </StandaloneLayout>
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
