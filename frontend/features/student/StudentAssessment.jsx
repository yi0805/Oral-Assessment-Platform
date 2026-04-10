import { useNavigate, useParams } from "react-router";
import { useEffect, useRef, useState } from "react";

import { useStartSession } from "./useStartSession";
import { getErrorMessage } from "../../utils/getErrorMessage";
import { useCourses } from "../../hooks/useCourses";
import { toRoman } from "../../utils/toRomanNumber";
import Loading from "../../ui/Loading";
import { useSubmitAnswer } from "./useSubmitAnswer";
import { useLogout } from "../authentication/useLogout";
import { useCompleteAssessment } from "./useCompleteAssessment";

export default function StudentAssessment() {
  const navigate = useNavigate();
  const { courseId, assessmentConfigId } = useParams();

  const [sessionId, setSessionId] = useState(null);
  const [assessmentTitle, setAssessmentTitle] = useState("");

  const [expiresAt, setExpiresAt] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);

  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [typedAnswer, setTypedAnswer] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [canComplete, setCanComplete] = useState(false);

  const [maxMainQuestions, setMaxMainQuestions] = useState(0);
  const [maxFollowupsPerMain, setMaxFollowupsPerMain] = useState(0);

  const hasAutoCompleted = useRef(false);

  const { courses, isLoading: isCoursesLoading } = useCourses();
  const course = courses.find((c) => c.id === courseId);

  const { startSession } = useStartSession();
  const { submitAnswer } = useSubmitAnswer();
  const { completeAssessment } = useCompleteAssessment();
  const { logout } = useLogout();

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        // console.log(assessmentConfigId);
        const Response = await startSession({ assessmentConfigId });
        if (cancelled) return;

        console.log(Response);

        setSessionId(Response.session_id);
        setAssessmentTitle(Response.assessment_title);
        setExpiresAt(new Date(Response.expires_at));
        // setExpiresAt(new Date(Date.now() + 60 * 1000 * 60));
        setCurrentQuestion(Response.current_question);
        setCanComplete(Response.can_complete ?? false);
        setMaxMainQuestions(Response.max_main_questions ?? 0);
        setMaxFollowupsPerMain(Response.max_followups_per_main ?? 0);
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

  useEffect(() => {
    if (!expiresAt) return;

    function tick() {
      const remaining = Math.max(
        0,
        Math.floor((expiresAt.getTime() - Date.now()) / 1000),
      );
      setTimeLeft(remaining);
    }

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  useEffect(() => {
    if (timeLeft == null) return;
    if (timeLeft > 0) return;
    if (!sessionId) return;
    if (hasAutoCompleted.current) return;
    if (isSubmitting) return;

    hasAutoCompleted.current = true;
    setIsSubmitting(true);

    async function autoComplete() {
      try {
        await completeAssessment({ sessionId });
        navigate(`/student/${courseId}`);
      } catch (error) {
        setError(getErrorMessage(error, "Failed to complete assessment."));
        setIsSubmitting(false);
      }
    }

    autoComplete();
  }, [
    timeLeft,
    sessionId,
    isSubmitting,
    completeAssessment,
    navigate,
    courseId,
  ]);

  if (isLoading || isCoursesLoading) return <Loading />;

  function formatTime(seconds) {
    if (seconds == null) return "--:--";

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(
      remainingSeconds,
    ).padStart(2, "0")}`;
  }

  async function handleSubmitAnswer() {
    console.log(course.id);
    if (!typedAnswer.trim() || isSubmitting) return;

    setIsSubmitting(true);

    try {
      const response = await submitAnswer({ sessionId, answer: typedAnswer });
      setTypedAnswer("");
      if (response.next_question) {
        setCurrentQuestion(response.next_question);
      } else {
        setCurrentQuestion(null);
        setCanComplete(true);
      }

      console.log(response);
    } catch (error) {
      setError(getErrorMessage(error, "Failed to submit answer."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCompleteSession() {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      await completeAssessment({ sessionId });
      navigate(`/student/${courseId}`);
    } catch (error) {
      setError(getErrorMessage(error, "Failed to complete assessment."));
    }
  }

  const mainGroupNo = currentQuestion?.main_group_no ?? 0;
  const followupNo = currentQuestion?.followup_no ?? 0;
  const isFollowupQuestion = currentQuestion?.question_kind === "followup";

  const questionKindLabel = isFollowupQuestion
    ? `Follow-up Question ${toRoman(followupNo) || ""}`.trim()
    : `Main Question ${mainGroupNo || ""}`.trim();

  const plannedMainQuestions = Array.from(
    { length: maxMainQuestions },
    (_, index) => index + 1,
  );

  // console.log(courseId, assessmentConfigId);
  // console.log(expiresAt, timeLeft);

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
              onClick={() => logout()}
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
            {error && (
              <div className="relative overflow-hidden rounded-xl border border-error/15 bg-error-container/40 p-8 shadow-sm">
                <div className="absolute left-0 top-0 h-full w-2 bg-error"></div>

                <div className="flex items-start gap-4">
                  <span
                    className="material-symbols-outlined text-4xl text-error"
                    style={{ fontVariationSettings: '"FILL" 1' }}
                  >
                    error
                  </span>

                  <div className="space-y-2">
                    <h2 className="font-headline text-2xl font-semibold text-on-background">
                      Something went wrong
                    </h2>
                    <p className="text-sm leading-relaxed text-on-surface-variant">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {canComplete && !currentQuestion && !error && (
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-8 shadow-sm">
                <div className="absolute left-0 top-0 h-full w-2 bg-secondary"></div>

                <div className="flex items-start gap-4">
                  <span
                    className="material-symbols-outlined text-4xl text-secondary"
                    style={{ fontVariationSettings: '"FILL" 1' }}
                  >
                    task_alt
                  </span>

                  <div className="space-y-2">
                    <h2 className="font-headline text-2xl font-semibold text-on-background">
                      All questions answered
                    </h2>
                    <p className="text-sm leading-relaxed text-on-surface-variant">
                      Your final answer has been saved. You can now submit and
                      complete the assessment.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {currentQuestion && (
              <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-8 shadow-sm">
                <div className="absolute left-0 top-0 h-full w-2 bg-primary"></div>
                <div className="mb-6 flex items-center gap-3">
                  <span className="rounded-full bg-primary-container px-3 py-1 text-xs font-bold text-on-primary-container">
                    {questionKindLabel}
                  </span>
                </div>
                <h2 className="mb-4 font-headline text-2xl font-semibold leading-snug text-on-background">
                  {currentQuestion?.asked_text}
                </h2>
              </div>
            )}

            {currentQuestion && (
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
            )}
          </div>

          <div className="space-y-6 md:col-span-4">
            <div className="space-y-6 rounded-xl bg-surface-container-low p-6">
              <div>
                <h3 className="mb-4 font-headline text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  Assessment Progress
                </h3>

                <div className="space-y-4">
                  {plannedMainQuestions.map((mainNo) => {
                    const isMainCompleted = mainNo < mainGroupNo;
                    const isMainCurrent = mainNo === mainGroupNo;

                    return (
                      <div key={mainNo} className="space-y-2">
                        <div
                          className={`flex items-center justify-between text-sm ${
                            isMainCurrent
                              ? "font-semibold text-primary"
                              : isMainCompleted
                                ? "text-on-surface"
                                : "text-outline"
                          }`}
                        >
                          <span>Main Question {mainNo}</span>

                          {isMainCompleted ? (
                            <span
                              className="material-symbols-outlined text-sm text-secondary"
                              style={{ fontVariationSettings: '"FILL" 1' }}
                            >
                              check_circle
                            </span>
                          ) : isMainCurrent ? (
                            <div className="h-2 w-2 rounded-full bg-primary"></div>
                          ) : (
                            <span className="material-symbols-outlined text-sm">
                              radio_button_unchecked
                            </span>
                          )}
                        </div>

                        {isMainCurrent && (
                          <div className="ml-4 space-y-1">
                            {Array.from(
                              { length: maxFollowupsPerMain },
                              (_, followupIndex) => followupIndex + 1,
                            ).map((followupStep) => {
                              const isFollowupCompleted =
                                isFollowupQuestion && followupStep < followupNo;

                              const isFollowupCurrent =
                                isFollowupQuestion &&
                                followupStep === followupNo;

                              return (
                                <div
                                  key={followupStep}
                                  className={`flex items-center justify-between text-xs ${
                                    isFollowupCurrent
                                      ? "font-semibold text-primary"
                                      : isFollowupCompleted
                                        ? "text-on-surface"
                                        : "text-outline"
                                  }`}
                                >
                                  <span>Follow-up {toRoman(followupStep)}</span>

                                  {isFollowupCompleted ? (
                                    <span
                                      className="material-symbols-outlined text-sm text-secondary"
                                      style={{
                                        fontVariationSettings: '"FILL" 1',
                                      }}
                                    >
                                      check_circle
                                    </span>
                                  ) : isFollowupCurrent ? (
                                    <div className="h-2 w-2 rounded-full bg-primary"></div>
                                  ) : (
                                    <span className="material-symbols-outlined text-sm">
                                      radio_button_unchecked
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              {currentQuestion && (
                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-4 font-bold text-on-primary shadow-sm transition-all hover:bg-primary-dim active:scale-[0.98] disabled:opacity-50"
                  onClick={handleSubmitAnswer}
                  disabled={isSubmitting || !typedAnswer.trim()}
                >
                  {isSubmitting ? "Submitting..." : "Submit Answer"}
                  <span className="material-symbols-outlined text-sm">
                    send
                  </span>
                </button>
              )}

              {canComplete && !currentQuestion && (
                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-secondary py-4 font-bold text-on-secondary shadow-sm transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
                  onClick={handleCompleteSession}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Submitting..." : "Submit Assessment"}
                  <span className="material-symbols-outlined text-sm">
                    check_circle
                  </span>
                </button>
              )}
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
