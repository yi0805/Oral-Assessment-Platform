import LoginChooser from "../features/authentication/LoginChooser";
import BaseCard from "../ui/BaseCard";
import StandaloneLayout from "../ui/StandaloneLayout";

function Login() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 sm:p-12 relative overflow-hidden ">
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary-container/20 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-5%] left-[-5%] w-[400px] h-[400px] bg-tertiary-container/30 rounded-full blur-[100px]"></div>
      </div>
      <StandaloneLayout>
        <BaseCard $variant="login">
          <LoginChooser />
        </BaseCard>
      </StandaloneLayout>
      <div className="fixed bottom-8 right-8 flex items-center gap-3 bg-surface-container-low px-4 py-2 rounded-full border border-outline-variant/10 shadow-sm">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
        <span className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">
          Systems Operational
        </span>
      </div>
    </div>
  );
}

export default Login;
