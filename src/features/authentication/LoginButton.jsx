import { useGoogleLogin } from "@react-oauth/google";
import toast from "react-hot-toast";

function LoginButton({ login }) {
  const googleLogin = useGoogleLogin({
    onSuccess: (tokenResponse) => login({ accessToken: tokenResponse.access_token }),
    onError: () => toast.error("Google sign-in failed. Please try again."),
  });

  return (
    <button
      type="button"
      className="group flex w-full items-center justify-center gap-3 rounded-xl border border-outline-variant/20 bg-surface-container-lowest px-6 py-4 font-semibold text-on-surface shadow-sm transition-all hover:border-primary/30 hover:bg-primary/5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary/30"
      onClick={() => googleLogin()}
    >
      <span className="material-symbols-outlined text-primary">login</span>
      Continue with Google
    </button>
  );
}

export default LoginButton;
