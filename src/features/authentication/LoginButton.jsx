import { useGoogleLogin } from "@react-oauth/google";

function LoginButton({ role, login }) {
  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      login({ accessToken: tokenResponse.access_token });
    },
    onError: (error) => console.error("Google login failed:", error),
  });

  return role === "student" ? (
    <button
      className="group relative flex flex-col items-center overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-10 text-left text-center shadow-sm transition-all duration-500 hover:border-primary/20 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-primary/20"
      onClick={() => googleLogin()}
    >
      <div className="absolute inset-0 bg-primary/0 transition-colors duration-500 group-hover:bg-primary/[0.02]"></div>
      <div className="relative z-10 mb-8 flex h-20 w-20 items-center justify-center rounded-full bg-surface-container transition-colors duration-500 group-hover:bg-primary-container">
        <span className="material-symbols-outlined text-4xl text-primary transition-transform duration-500 group-hover:scale-110">
          person
        </span>
      </div>
      <div className="relative z-10">
        <h2 className="headline-font mb-3 text-2xl font-bold text-on-surface">
          Login as Student
        </h2>
        <ul className="mx-auto mb-8 max-w-xs space-y-1 text-center font-body text-sm leading-relaxed text-on-surface-variant">
          <li className="before:mr-2 before:content-['•']">
            Access your assigned oral exams
          </li>
          <li className="before:mr-2 before:content-['•']">
            Review your session history
          </li>
          <li className="before:mr-2 before:content-['•']">
            View personalized feedback
          </li>
        </ul>
        <div className="flex items-center justify-center gap-2 font-semibold text-primary transition-all duration-300 group-hover:gap-4">
          <span>Continue to Portal</span>
          <span className="material-symbols-outlined text-lg">
            arrow_forward
          </span>
        </div>
      </div>

      <div className="absolute -bottom-10 -right-10 opacity-5 transition-opacity duration-700 group-hover:opacity-10">
        <img
          alt="student study session"
          className="h-48 w-48 rounded-full object-cover grayscale"
          data-alt="abstract monochromatic photograph of an open notebook with soft shadows and a pen resting on it in a quiet library"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDwtE8W3GNjjkAcxUjcJMBK9v5s_E7CrrovwYm0Zsb30bNeoy6MehzuFqydCQJ67zkf_QsIeKeBWqzizAH4FbTHeorvrLe8a8INyGT26YExxwQBPzQEgWImSLtoWaRuGs_rf5couZ7EMp31tf_pzilf0bI0mzgngkQaPAQBA2638ry0adGulBEfHsFKfqXiKRvpel3tWbnZP03RFO7WBLokXiqFeAzVaXXBTEALQc4d2lrmZFOyiefJW4g_Ex47PeBzBDupCiAoPYYw"
        />
      </div>
    </button>
  ) : (
    <button
      className="group relative flex flex-col items-center overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-10 text-left text-center shadow-sm transition-all duration-500 hover:border-primary/20 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-primary/20"
      onClick={() => googleLogin()}
    >
      <div className="absolute inset-0 bg-primary/0 transition-colors duration-500 group-hover:bg-primary/[0.02]"></div>
      <div className="relative z-10 mb-8 flex h-20 w-20 items-center justify-center rounded-full bg-surface-container transition-colors duration-500 group-hover:bg-secondary-container">
        <span className="material-symbols-outlined text-4xl text-secondary transition-transform duration-500 group-hover:scale-110">
          account_balance
        </span>
      </div>
      <div className="relative z-10">
        <h2 className="headline-font mb-3 text-2xl font-bold text-on-surface">
          Login as Instructor
        </h2>
        <ul className="mx-auto mb-8 max-w-xs space-y-1 text-center font-body text-sm leading-relaxed text-on-surface-variant">
          <li className="before:mr-2 before:content-['•']">
            Manage course curriculums
          </li>
          <li className="before:mr-2 before:content-['•']">
            Design assessment rubrics
          </li>
          <li className="before:mr-2 before:content-['•']">
            Grade student performances
          </li>
        </ul>
        <div className="flex items-center justify-center gap-2 font-semibold text-secondary transition-all duration-300 group-hover:gap-4">
          <span>Curator Portal</span>
          <span className="material-symbols-outlined text-lg">
            arrow_forward
          </span>
        </div>
      </div>

      <div className="absolute -bottom-10 -right-10 opacity-5 transition-opacity duration-700 group-hover:opacity-10">
        <img
          alt="academic administration"
          className="h-48 w-48 rounded-full object-cover grayscale"
          data-alt="monochromatic minimalist shot of a architectural hallway with strong perspective lines and soft professional lighting"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuBuzgXrfoL3k8XWUkGo-dOCzsNrEjiZu4QLhcTulxwcKa4KgFmqjG-O4ZHuzkOq7jCV7WZuE5HwYHcDZSte1xwWyaCHRK6B9QTJRJnJXERtkkjYQWXRrBlXkAvs1lgdviVJEmxEa5A-6ESczJoJAp_CQokLu1hRk8e2FC8OVKt1lvHQCm5BTfpKKwRU3KxMJIJ_9wQSMR83r14OFSySy0w8Iibw_QLivVyKsxmHnYxytceK4ytreW_jxWXQTLDhnw-vwhr-m6WqZXuR"
        />
      </div>
    </button>
  );
}

export default LoginButton;
