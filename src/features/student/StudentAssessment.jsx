import { useLocation, useNavigate, useParams } from "react-router";
import { useEffect, useRef, useState } from "react";
import { googleLogout } from "@react-oauth/google";

import { useStartSession } from "./useStartSession";
import { getErrorMessage } from "../../utils/getErrorMessage";
import { useCourses } from "../../hooks/useCourses";
import Loading from "../../ui/Loading";

export default function StudentAssessment() {
  const navigate = useNavigate();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [sessionId, setSessionId] = useState(null);
  const [assessmentTitle, setAssessmentTitle] = useState("");

  const [expiresAt, setExpiresAt] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);

  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [typedAnswer, setTypedAnswer] = useState("");

  const [sessionStatus, setSessionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const { courseId, assessmentConfigId } = useParams();

  const { startSession } = useStartSession();
  const { courses, isLoading: isCoursesLoading } = useCourses();
  const course = courses.find((c) => c.id === courseId);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        console.log(assessmentConfigId);
        const Response = await startSession({ assessmentConfigId });
        if (cancelled) return;

        console.log(Response);

        setSessionId(Response.session_id);
        setAssessmentTitle(Response.assessment_title);
        // setExpiresAt(new Date(Response.expires_at));
        setExpiresAt(new Date(Date.now() + 60 * 1000 * 60));
        setCurrentQuestion(Response.first_question);
        setSessionStatus("in_progress");
      } catch (err) {
        if (cancelled) return;
        setError(getErrorMessage(err, "Failed to start the assessment."));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [assessmentConfigId, startSession]);

  // useEffect(() => {
  //   if (!expiresAt) return;

  //   function tick() {
  //     const remaining = Math.max(
  //       0,
  //       Math.floor((expiresAt.getTime() - Date.now()) / 1000),
  //     );
  //     setTimeLeft(remaining);
  //   }

  //   tick();
  //   const id = setInterval(tick, 1000);
  //   return () => clearInterval(id);
  // }, [expiresAt]);

  if (isLoading || isCoursesLoading) return <Loading />;

  function formatTime(seconds) {
    if (seconds == null) return "--:--";

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(
      remainingSeconds,
    ).padStart(2, "0")}`;
  }

  const questionKindLabel =
    currentQuestion?.question_kind === "followup"
      ? "Follow-up Question"
      : `Main Question ${currentQuestion?.main_group_no ?? ""}`;

  // const totalQuestions =
  // const currentQuestion =
  // const progressPercent = ((currentQuestionIndex + 1) / totalQuestions) * 100;

  console.log(courseId, assessmentConfigId);
  console.log(expiresAt, timeLeft);

  // const handleLogout = () => {
  //   localStorage.removeItem("role");
  //   localStorage.removeItem("userName");
  //   localStorage.removeItem("userPicture");
  //   googleLogout();
  //   navigate("/login");
  // };

  // const handleSubmitAnswer = () => {
  //   if (currentQuestionIndex < totalQuestions - 1) {
  //     setCurrentQuestionIndex((prev) => prev + 1);
  //     setTypedAnswer("");
  //   } else {
  //     assessment.status = "Completed";
  //     navigate(`/student/${courseId}`, { state: { studentName, courseId } });
  //   }
  // };

  return (
    <div className="font-body selection:bg-primary-container selection:text-on-primary-container">
      <header className="fixed top-0 z-40 flex h-16 w-full items-center justify-between bg-[#f8f9fa] px-8">
        <div className="flex items-center gap-4">
          <span className="font-headline text-xl font-bold tracking-tight text-[#4f6073]">
            WhereRU
          </span>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-[#586064]">
            <span className="material-symbols-outlined">timer</span>
            <span
              className={`font-label text-sm font-medium ${timeLeft != null && timeLeft < 60 ? "text-error" : ""}`}
            >
              {formatTime(timeLeft)}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="material-symbols-outlined cursor-pointer rounded-full p-2 text-[#4f6073] transition-colors hover:bg-[#eaeff1]">
              notifications
            </span>
            <span className="material-symbols-outlined cursor-pointer rounded-full p-2 text-[#4f6073] transition-colors hover:bg-[#eaeff1]">
              help
            </span>
            <button
              className="rounded-lg px-4 py-2 text-sm font-semibold text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95"
              // onClick={() => handleLogout()}
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="flex min-h-screen flex-col items-center px-6 pb-12 pt-24">
        <div className="mb-12 w-full max-w-4xl">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface-variant">
            {course
              ? `${course.course_code} • ${course.course_name}`
              : "Unknown Course"}
          </p>
          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-primary">
            {assessmentTitle}
          </h1>
        </div>
        <div className="grid w-full max-w-4xl grid-cols-1 gap-8 md:grid-cols-12">
          <div className="space-y-8 md:col-span-8">
            {currentQuestion && (
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-8 shadow-sm">
                <div className="absolute left-0 top-0 h-full w-2 bg-primary"></div>
                <div className="mb-6 flex items-center gap-3">
                  <span className="rounded-full bg-primary-container px-3 py-1 text-xs font-bold text-on-primary-container">
                    {/* Question {currentQuestionIndex + 1} of {totalQuestions} */}
                    {questionKindLabel}
                  </span>
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-surface-container">
                    <div
                      className="h-full bg-primary"
                      // style={{ width: `${progressPercent}%` }}
                    ></div>
                  </div>
                </div>
                <h2 className="mb-4 font-headline text-2xl font-semibold leading-snug text-on-background">
                  {currentQuestion?.asked_text}
                </h2>
              </div>
            )}

            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center rounded-xl border border-outline-variant/10 bg-surface-container-low p-10">
                <p className="mb-8 font-medium text-on-surface-variant">
                  Tap the microphone to speak your answer
                </p>
                <div className="relative">
                  <div className="absolute -inset-4 rounded-full bg-primary/5 blur-xl"></div>
                  <button className="relative flex h-24 w-24 items-center justify-center rounded-full bg-primary text-on-primary shadow-lg transition-all hover:bg-primary-dim active:scale-95">
                    <span
                      className="material-symbols-outlined text-4xl"
                      data-weight="fill"
                      style={{ fontVariationSettings: '"FILL" 1' }}
                    >
                      mic
                    </span>
                  </button>
                </div>
                <div className="mt-8 flex gap-2">
                  <div className="h-4 w-1 rounded-full bg-primary/20"></div>
                  <div className="h-8 w-1 rounded-full bg-primary/40"></div>
                  <div className="h-12 w-1 rounded-full bg-primary"></div>
                  <div className="h-6 w-1 rounded-full bg-primary/60"></div>
                  <div className="h-10 w-1 rounded-full bg-primary/80"></div>
                </div>
              </div>

              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-4 flex items-center">
                  <span className="material-symbols-outlined text-outline">
                    keyboard
                  </span>
                </div>
                <textarea
                  className="block w-full rounded-xl border border-outline-variant/20 bg-surface-container-lowest py-4 pl-12 pr-4 font-body text-sm placeholder:text-outline-variant focus:border-primary focus:ring-primary"
                  placeholder="Type your response here if you prefer not to use voice..."
                  rows="4"
                  value={typedAnswer}
                  onChange={(e) => setTypedAnswer(e.target.value)}
                  onCopy={(e) => e.preventDefault()}
                  onPaste={(e) => e.preventDefault()}
                  onCut={(e) => e.preventDefault()}
                  onKeyDown={(e) => {
                    if (
                      (e.ctrlKey || e.metaKey) &&
                      ["c", "v", "x"].includes(e.key.toLowerCase())
                    ) {
                      e.preventDefault();
                    }
                  }}
                ></textarea>
              </div>
            </div>
          </div>

          <div className="space-y-6 md:col-span-4">
            <div className="space-y-6 rounded-xl bg-surface-container-low p-6">
              <div>
                <h3 className="mb-4 font-headline text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  Assessment Progress
                </h3>

                <div className="space-y-3">
                  {/* {assessment.questions.map((question, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between text-sm ${
                        index === currentQuestionIndex
                          ? "font-semibold"
                          : index < currentQuestionIndex
                            ? "text-on-surface"
                            : "text-outline"
                      }`}
                    >
                      <span
                        className={
                          index === currentQuestionIndex
                            ? "text-primary"
                            : "text-on-surface"
                        }
                      >
                        Question {index + 1}
                      </span>

                      {index < currentQuestionIndex ? (
                        <span
                          className="material-symbols-outlined text-sm text-secondary"
                          style={{ fontVariationSettings: '"FILL" 1' }}
                        >
                          check_circle
                        </span>
                      ) : index === currentQuestionIndex ? (
                        <div className="h-2 w-2 rounded-full bg-primary"></div>
                      ) : (
                        <span className="material-symbols-outlined text-sm">
                          radio_button_unchecked
                        </span>
                      )}
                    </div>
                  ))} */}
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <button
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-4 font-bold text-on-primary shadow-sm transition-all hover:bg-primary-dim active:scale-[0.98]"
                // onClick={handleSubmitAnswer}
              >
                Submit Answer
                <span className="material-symbols-outlined text-sm">send</span>
              </button>
            </div>

            <div className="rounded-xl bg-tertiary-container/30 p-6">
              <div className="mb-2 flex items-center gap-2 text-on-tertiary-container">
                <span className="material-symbols-outlined text-sm">info</span>
                <span className="text-xs font-bold uppercase tracking-wider">
                  Curator's Tip
                </span>
              </div>
              <p className="text-xs leading-relaxed text-on-tertiary-container/80">
                Try to structure your answer using the 'Statement, Explanation,
                Example' framework for higher clarity scoring.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
