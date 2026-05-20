import { useNavigate, useParams } from "react-router";
import { useEffect, useRef, useState } from "react";

import { useStartSession } from "./useStartSession";
import { useCourses } from "../../hooks/useCourses";
import { useSubmitAnswer } from "./useSubmitAnswer";
import { useTranscribeAudio } from "./useTranscribeAudio";
import { useAudioRecorder } from "./useAudioRecorder";
import { useLogout } from "../authentication/useLogout";
import { useCompleteAssessment } from "./useCompleteAssessment";
import { useStudentSpeechStream } from "./useStudentSpeechStream";
import { useRecordBlurNotification } from "./useRecordBlurNotification";
import { useRecordReconnect } from "./useRecordReconnect";

// [STT #72] Streaming path is the default after the rollout in
// commit 28 of feature/audio-to-text. Set VITE_STT_STREAMING=0 in
// .env.local to force the legacy batch-only behaviour for debugging
// (the batch path is intact and used as the automatic fallback when
// the WebSocket errors — see useStudentSpeechStream.js).
const STREAMING_ENABLED = import.meta.env.VITE_STT_STREAMING !== "0";

import Loading from "../../ui/Loading";
import ConfirmModal from "../../ui/ConfirmModal";
import { toRoman } from "../../utils/toRomanNumber";
import { getErrorMessage } from "../../utils/getErrorMessage";

export default function StudentAssessment() {
  const navigate = useNavigate();

  const { courseId, assessmentConfigId } = useParams();

  const {
    session,
    isLoading: isSessionLoading,
    isFetching: isSessionFetching,
    error: sessionError,
    refetch: refetchSession,
  } = useStartSession(assessmentConfigId);

  const sessionId = session?.session_id ?? null;
  const assessmentTitle = session?.assessment_title ?? "";
  const expiresAtIso = session?.expires_at ?? null;
  const maxMainQuestions = session?.main_question_num ?? 0;
  const maxFollowupsPerMain = session?.follow_up_num ?? 0;

  const [timeLeft, setTimeLeft] = useState(null);

  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [typedAnswer, setTypedAnswer] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [error, setError] = useState(null);
  const [audioError, setAudioError] = useState(null);

  const [isSpeaking, setIsSpeaking] = useState(false);

  const [canComplete, setCanComplete] = useState(false);

  const [blurCount, setBlurCount] = useState(0);

  const [disconnectCount, setDisconnectCount] = useState(0);

  const hasAutoCompleted = useRef(false);
  const autoRetryTimerRef = useRef(null);
  const [retryNonce, setRetryNonce] = useState(0);

  // [STT #72] Set to true when the student presses Esc during an
  // in-flight batch transcription. The fetch can't actually be
  // aborted client-side, but checking this ref after the await lets
  // us discard the eventual transcript instead of clobbering the
  // textarea with stale text.
  const transcribeCancelledRef = useRef(false);

  const { courses, isLoading: isCoursesLoading } = useCourses();
  const course = courses.find((c) => c.id === courseId);

  const { submitAnswer } = useSubmitAnswer();
  const { transcribeAudio, isPending: batchIsTranscribing } =
    useTranscribeAudio();
  const {
    status: recordingStatus,
    isSupported: isAudioSupported,
    start: startRecording,
    stop: stopRecording,
    reset: resetRecorder,
  } = useAudioRecorder();
  const { completeAssessment } = useCompleteAssessment();
  const { recordBlurNotification } = useRecordBlurNotification();
  const { recordReconnectNotification } = useRecordReconnect();

  // [STT #72] Streaming hook is always instantiated so React's
  // rules-of-hooks stay happy; the rest of the component branches on
  // STREAMING_ENABLED to decide whether to use it.
  const speech = useStudentSpeechStream();

  const { logout, isPending: isLoggingOut } = useLogout();

  const [confirmingLogout, setConfirmingLogout] = useState(false);

  // [STT #72] Unified "isRecording" / "isTranscribing" derived from
  // whichever flow is active. Downstream UI (mic-button styling,
  // textarea disabled state, audioBusy guards) reads these names
  // exactly as before, so the JSX below doesn't have to branch.
  const isRecording = STREAMING_ENABLED
    ? speech.status === "connecting" || speech.status === "streaming"
    : recordingStatus === "recording";
  const isTranscribing = STREAMING_ENABLED
    ? speech.status === "stopping"
    : batchIsTranscribing;
  const audioBusy = isRecording || isTranscribing;

  const ttsSupported =
    typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    if (!session) return;
    setCurrentQuestion(session.current_question);
    setCanComplete(session.can_complete ?? false);
  }, [session]);

  useEffect(() => {
    if (!expiresAtIso) return;

    const expiresAtMs = new Date(expiresAtIso).getTime();

    function tick() {
      const remaining = Math.max(
        0,
        Math.floor((expiresAtMs - Date.now()) / 1000),
      );
      setTimeLeft(remaining);
    }

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAtIso]);

  useEffect(() => {
    function handleVisibilityChange() {
      if (document.visibilityState === "hidden") {
        setBlurCount((count) => count + 1);
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const offlineKey = `assessment_offline_${sessionId}`;
    const countKey = `assessment_reconnects_${sessionId}`;

    let restored = Number(localStorage.getItem(countKey)) || 0;

    if (localStorage.getItem(offlineKey) && navigator.onLine) {
      localStorage.removeItem(offlineKey);
      restored += 1;
      localStorage.setItem(countKey, String(restored));
    }

    setDisconnectCount(restored);
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;

    const offlineKey = `assessment_offline_${sessionId}`;
    const countKey = `assessment_reconnects_${sessionId}`;

    function handleOffline() {
      localStorage.setItem(offlineKey, "1");
    }

    function handleOnline() {
      if (!localStorage.getItem(offlineKey)) return;

      localStorage.removeItem(offlineKey);
      setDisconnectCount((count) => {
        const next = count + 1;
        localStorage.setItem(countKey, String(next));
        return next;
      });
    }

    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);

    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [sessionId]);

  useEffect(() => {
    if (timeLeft == null) return;
    if (timeLeft > 0) return;
    if (!sessionId) return;
    if (hasAutoCompleted.current) return;
    if (isSubmitting) return;
    if (isTranscribing) return;

    hasAutoCompleted.current = true;
    setIsSubmitting(true);

    async function autoComplete() {
      try {
        if (typedAnswer.trim() && !isRecording && !isTranscribing) {
          try {
            await submitAnswer({ sessionId, answer: typedAnswer });
          } catch {
            //do not block completion
          }
        }

        if (blurCount > 0) {
          try {
            await recordBlurNotification({ sessionId, blurCount });
          } catch (blurError) {
            setError(
              getErrorMessage(
                blurError,
                "Failed to record tab-switch notification.",
              ),
            );
          }
        }

        if (disconnectCount > 0) {
          try {
            await recordReconnectNotification({ sessionId, disconnectCount });
          } catch (reconnectError) {
            setError(
              getErrorMessage(
                reconnectError,
                "Failed to record reconnect notification.",
              ),
            );
          }
        }

        await completeAssessment({ sessionId, courseId });
        localStorage.removeItem(`assessment_reconnects_${sessionId}`);
        localStorage.removeItem(`assessment_offline_${sessionId}`);
        navigate(`/student/${courseId}`);
      } catch (error) {
        setError(getErrorMessage(error, "Failed to submit assessment."));
        setIsSubmitting(false);
        if (retryNonce < 2) {
          const delay = retryNonce === 0 ? 5000 : 15000;
          autoRetryTimerRef.current = setTimeout(() => {
            hasAutoCompleted.current = false;
            setRetryNonce((n) => n + 1);
          }, delay);
        }
      }
    }

    autoComplete();
  }, [
    timeLeft,
    sessionId,
    isSubmitting,
    isTranscribing,
    isRecording,
    completeAssessment,
    recordBlurNotification,
    recordReconnectNotification,
    submitAnswer,
    blurCount,
    disconnectCount,
    typedAnswer,
    navigate,
    courseId,
    retryNonce,
  ]);

  // [STT #72] Surface streaming errors (e.g. AWS dropped the
  // connection mid-stream) into the existing audioError banner so the
  // student isn't left wondering why partials stopped appearing.
  // handleMicClick also catches errors at start/stop boundaries; this
  // effect covers the in-between case.
  useEffect(() => {
    if (!STREAMING_ENABLED) return;
    if (!speech.error) return;
    setAudioError(
      getErrorMessage(speech.error, "Streaming transcription error."),
    );
  }, [speech.error]);

  // Auto-stop handling. When the WebSocket dies before the student
  // pressed stop (server-enforced duration cap, abnormal close), the
  // orchestrator runs the buffered-audio fallback and exposes
  // autoStopReason + the transcript via speech.final. The mic flow
  // never gets a chance to call setTypedAnswer because there's no
  // awaited stop() to return the text — surface it here instead, plus
  // an informational banner so the student knows what happened.
  const autoStopHandledRef = useRef(false);
  useEffect(() => {
    if (!STREAMING_ENABLED) return;
    if (!speech.autoStopReason) {
      autoStopHandledRef.current = false;
      return;
    }
    // Wait until the fallback has finished and the orchestrator has
    // settled back to idle / error before reacting — speech.final is
    // only populated once the batch transcribe round-trip completes.
    if (speech.status !== "idle" && speech.status !== "error") return;
    if (autoStopHandledRef.current) return;
    autoStopHandledRef.current = true;

    if (speech.final && speech.final.trim()) {
      // Overwrite to match the user-initiated stop flow's behaviour.
      setTypedAnswer(speech.final.trim());
    }

    setAudioError(
      speech.autoStopReason === "session_timeout"
        ? "Recording stopped automatically after the maximum duration. We saved what was captured — review it below and submit."
        : "The recording connection dropped, so we stopped automatically and recovered what was captured. Review the text below and submit, or record again.",
    );
  }, [speech.autoStopReason, speech.final, speech.status]);

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel();
      setIsSpeaking(false);
    };
  }, [currentQuestion?.question_text]);

  useEffect(() => {
    if (isRecording) {
      window.speechSynthesis?.cancel();
      setIsSpeaking(false);
    }
  }, [isRecording]);

  // [STT #72] Elapsed-time counter for the "Transcribing…" indicator.
  // Driven by the derived isTranscribing, so it covers both the
  // batch path (waiting for AWS Transcribe job to complete) and the
  // streaming path (waiting for the final flush after the user hits
  // stop).
  const [transcribingElapsedSec, setTranscribingElapsedSec] = useState(0);
  useEffect(() => {
    if (!isTranscribing) {
      setTranscribingElapsedSec(0);
      return undefined;
    }
    // performance.now() rather than Date.now() so the counter is
    // unaffected by the user's system clock drifting / changing.
    const startMs = performance.now();
    setTranscribingElapsedSec(0);
    const id = setInterval(() => {
      setTranscribingElapsedSec(
        Math.floor((performance.now() - startMs) / 1000),
      );
    }, 1000);
    return () => clearInterval(id);
  }, [isTranscribing]);

  // [STT #72] Esc-to-cancel for the in-flight recording / transcription.
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key !== "Escape") return;
      if (!isRecording && !isTranscribing) return;

      event.preventDefault();
      transcribeCancelledRef.current = true;

      if (STREAMING_ENABLED) {
        speech.cancel();
        speech.reset();
      } else if (isRecording) {
        resetRecorder();
      }

      setAudioError(null);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isRecording, isTranscribing, resetRecorder, speech]);

  // Integration: clear the auto-submit retry timer on unmount so a
  // user navigating away while a retry is queued doesn't fire it
  // against a stale session.
  useEffect(
    () => () => {
      if (autoRetryTimerRef.current) clearTimeout(autoRetryTimerRef.current);
    },
    [],
  );

  if (isSessionLoading || isCoursesLoading) return <Loading />;

  const displayedError =
    error ||
    (sessionError
      ? getErrorMessage(sessionError, "Failed to start the assessment.")
      : null);

  function formatTime(seconds) {
    if (seconds == null) return "--:--";

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(
      remainingSeconds,
    ).padStart(2, "0")}`;
  }

  async function handleSubmitAnswer() {
    // Trim once at the boundary so what the server stores matches what
    // the student saw. Re-checks isSubmitting for the (rare) case where
    // a click slips through before the disabled prop renders.
    const trimmedAnswer = typedAnswer.trim();
    if (!trimmedAnswer || isSubmitting) return;

    // Clear any lingering transcription error so it doesn't sit on the
    // page after a successful submit (#71).
    setAudioError(null);
    setIsSubmitting(true);

    try {
      const response = await submitAnswer({
        sessionId,
        answer: trimmedAnswer,
      });

      setTypedAnswer("");
      // [STT #72] Clear any stale partial/final from the previous
      // question so the next one starts fresh.
      if (STREAMING_ENABLED) speech.reset();

      if (response.next_question) {
        setCurrentQuestion(response.next_question);
      } else {
        setCurrentQuestion(null);
        setCanComplete(true);
      }
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
      if (blurCount > 0 && sessionId) {
        try {
          await recordBlurNotification({ sessionId, blurCount });
        } catch (blurError) {
          setError(
            getErrorMessage(
              blurError,
              "Failed to record tab-switch notification.",
            ),
          );
        }
      }

      if (disconnectCount > 0 && sessionId) {
        try {
          await recordReconnectNotification({ sessionId, disconnectCount });
        } catch (reconnectError) {
          setError(
            getErrorMessage(
              reconnectError,
              "Failed to record reconnect notification.",
            ),
          );
        }
      }

      await completeAssessment({ sessionId, courseId });
      localStorage.removeItem(`assessment_reconnects_${sessionId}`);
      localStorage.removeItem(`assessment_offline_${sessionId}`);
      navigate(`/student/${courseId}`);
    } catch (error) {
      setError(getErrorMessage(error, "Failed to complete assessment."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSpeakQuestion() {
    if (!currentQuestion?.question_text) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(
      currentQuestion.question_text,
    );
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  // Issue #71 — transcribe-then-edit flow.
  //
  // Takes a finalized recording Blob, runs it through the transcribe-only
  // backend endpoint, and drops the result into the answer textarea. The
  // DB write happens later when the student clicks "Submit Answer" via
  // handleSubmitAnswer. This function never persists or advances the
  // session by itself.
  async function handleAudioSubmit(blob) {
    // [STT #72] Reset the cancel flag for this attempt. Pressing Esc
    // during the await below will flip it back to true and we'll
    // discard the result when it finally arrives.
    transcribeCancelledRef.current = false;
    try {
      const transcript = await transcribeAudio({
        sessionId,
        audioBlob: blob,
      });

      if (transcribeCancelledRef.current) {
        // The student cancelled mid-flight. Drop the transcript on
        // the floor — the cancel handler already cleared error state
        // and the UI has returned to "Tap the microphone to speak".
        return;
      }

      if (!transcript || !transcript.trim()) {
        // Don't clobber any existing typed text the student already
        // wrote — just surface a hint and leave the textarea alone.
        setAudioError(
          "We didn't catch any speech. Please try recording again.",
        );
        return;
      }

      // Overwrite (not append) so each new recording fully replaces the
      // previous draft. The student can then edit.
      setTypedAnswer(transcript);
    } catch (err) {
      // If the cancel happened to race with a network failure, prefer
      // the cancel — silent is the right UX when the student asked
      // us to stop.
      if (transcribeCancelledRef.current) return;
      setAudioError(getErrorMessage(err, "Failed to transcribe your audio."));
    }
  }

  // [STT #72] Streaming variant of the mic-button flow. Connects the
  // WebSocket, opens the mic, and (on second click) flushes the
  // server's remaining results before dropping the final transcript
  // into typedAnswer. Behaviourally a drop-in replacement for the
  // batch flow below; we keep them as siblings so the feature flag
  // can flip back to batch with a single env-var change.
  async function handleMicClickStreaming() {
    if (speech.status === "connecting" || speech.status === "stopping") {
      return;
    }

    setAudioError(null);

    if (speech.status === "streaming") {
      try {
        const finalText = await speech.stop();

        // Esc pressed during await: discard the transcript instead of
        // overwriting typedAnswer. Mirrors the batch path in handleAudioSubmit.
        if (transcribeCancelledRef.current) return;
        if (finalText && finalText.trim()) {
          // Overwrite typedAnswer to match the batch flow's behaviour
          // (handleAudioSubmit), so each new recording fully replaces
          // the previous draft and the student can edit from there.
          setTypedAnswer(finalText.trim());
        } else if (speech.partial && speech.partial.trim()) {
          // No final transcript, but AWS sent some partial guesses along
          // the way. Use the last guess — it might be wrong, but letting
          // the student fix it beats losing their answer entirely.
          setTypedAnswer(speech.partial.trim());
        } else {
          // No final, no partial, no fallback transcript.
          setAudioError(
            "Transcription returned no text. Try speaking a bit longer or check your microphone.",
          );
        }
      } catch (err) {
        if (transcribeCancelledRef.current) return;
        setAudioError(getErrorMessage(err, "Streaming transcription failed."));
      } finally {
        speech.reset();
      }
      return;
    }

    if (!speech.isSupported) {
      setAudioError(
        "Real-time transcription isn't supported in this browser. Please type your answer instead.",
      );
      return;
    }

    try {
      // Reset for the new recording so a stale Esc flag from a previous
      // stop doesn't suppress this recording's transcript when the
      // student eventually stops it.
      transcribeCancelledRef.current = false;
      speech.reset();
      await speech.start(sessionId);
    } catch (err) {
      const name = err && err.name;

      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setAudioError(
          "Microphone access was blocked. Please allow microphone access in your browser and try again.",
        );
      } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
        setAudioError(
          "No microphone was detected. Please connect one and try again.",
        );
      } else {
        setAudioError(
          getErrorMessage(err, "Failed to start streaming transcription."),
        );
      }
    }
  }

  // Mic-button lifecycle only. Responsible for starting/stopping the
  // recorder and producing a Blob; persistence is delegated to
  // handleAudioSubmit so the two halves can evolve independently.
  async function handleMicClick() {
    if (!currentQuestion) return;
    if (isSubmitting) return;

    // [STT #72] When streaming is enabled, the whole mic flow is
    // delegated to handleMicClickStreaming and the batch path below
    // is unreachable.
    if (STREAMING_ENABLED) {
      await handleMicClickStreaming();
      return;
    }

    if (isTranscribing) return;

    setAudioError(null);

    if (isRecording) {
      const blob = await stopRecording();

      if (!blob || blob.size === 0) {
        setAudioError("No audio was captured. Please try again.");
        return;
      }

      await handleAudioSubmit(blob);
      return;
    }

    if (!isAudioSupported) {
      setAudioError(
        "Audio recording isn't supported in this browser. Please type your answer instead.",
      );
      return;
    }

    try {
      await startRecording();
    } catch (err) {
      const name = err && err.name;

      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setAudioError(
          "Microphone access was blocked. Please allow microphone access in your browser and try again.",
        );
      } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
        setAudioError(
          "No microphone was detected. Please connect one and try again.",
        );
      } else {
        setAudioError(getErrorMessage(err, "Failed to start recording."));
      }

      resetRecorder();
    }
  }

  const mainGroupNo = currentQuestion?.main_group_no ?? 0;
  const followupNo = currentQuestion?.followup_no ?? 0;
  const isFollowupQuestion = currentQuestion?.question_kind === "followup";
  const timerExpired = timeLeft != null && timeLeft <= 0;

  const questionKindLabel = isFollowupQuestion
    ? `Follow-up Question ${toRoman(followupNo) || ""}`.trim()
    : `Main Question ${mainGroupNo || ""}`.trim();

  const plannedMainQuestions = Array.from(
    { length: maxMainQuestions },
    (_, index) => index + 1,
  );

  return (
    <div className="font-body selection:bg-primary-container selection:text-on-primary-container">
      {confirmingLogout && (
        <ConfirmModal
          title="Log out of assessment?"
          message="The assessment timer keeps running after you log out, and the assessment will be submitted automatically when time runs out. Are you sure you want to log out?"
          confirmLabel="Yes, log out"
          loadingLabel="Logging out…"
          isLoading={isLoggingOut}
          onConfirm={() => logout()}
          onCancel={() => setConfirmingLogout(false)}
        />
      )}

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
              className={`font-label text-sm font-medium ${timeLeft != null && timeLeft < 30 ? "text-error" : ""}`}
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
              onClick={() => setConfirmingLogout(true)}
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
              : "Course Name Not Available"}
          </p>

          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-primary">
            {assessmentTitle || "Assessment Title Not Available"}
          </h1>

          {/* <p className="mt-2 text-xs text-on-surface-variant">
            Assessment timer continues if you logout or disconnect.
          </p> */}
        </div>

        <div className="grid w-full max-w-4xl grid-cols-1 gap-8 md:grid-cols-12">
          <div className="space-y-8 md:col-span-8">
            {blurCount > 0 && (
              <div className="rounded-xl border border-error/15 bg-error-container/40 p-4 text-sm text-on-background">
                You have left this tab {blurCount} time
                {blurCount === 1 ? "" : "s"} during the assessment. Repeated tab
                switching may be reported to your instructor.
              </div>
            )}

            {displayedError && (
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
                      Oops, something went wrong
                    </h2>

                    <p className="text-sm leading-relaxed text-on-surface-variant">
                      {displayedError}
                    </p>

                    {sessionError && !session && (
                      <button
                        type="button"
                        onClick={() => refetchSession()}
                        disabled={isSessionFetching}
                        className="mt-2 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-on-primary shadow-sm transition-all hover:bg-primary-dim active:scale-[0.98] disabled:opacity-50"
                      >
                        <span className="material-symbols-outlined text-sm">
                          refresh
                        </span>
                        {isSessionFetching ? "Retrying..." : "Try again"}
                      </button>
                    )}
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

                <div className="mb-6 flex items-center justify-between gap-3">
                  <span className="rounded-full bg-primary-container px-3 py-1 text-xs font-bold text-on-primary-container">
                    {questionKindLabel}
                  </span>

                  {ttsSupported && (
                    <button
                      type="button"
                      onClick={handleSpeakQuestion}
                      disabled={audioBusy}
                      aria-label={
                        isSpeaking
                          ? "Stop reading question"
                          : "Read question aloud"
                      }
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 ${
                        isSpeaking
                          ? "bg-secondary-container text-on-secondary-container"
                          : "text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
                      }`}
                    >
                      <span
                        className="material-symbols-outlined text-xl"
                        style={
                          isSpeaking
                            ? { fontVariationSettings: '"FILL" 1' }
                            : undefined
                        }
                      >
                        {isSpeaking ? "stop_circle" : "volume_up"}
                      </span>
                    </button>
                  )}
                </div>

                <h2 className="mb-4 select-none font-headline text-2xl font-semibold leading-snug text-on-background">
                  {currentQuestion?.question_text}
                </h2>
              </div>
            )}

            {currentQuestion && (
              <div className="space-y-6">
                <div className="flex flex-col items-center justify-center rounded-xl border border-outline-variant/10 bg-surface-container-low p-10">
                  <p className="mb-8 font-medium text-on-surface-variant">
                    {isTranscribing ? (
                      <>
                        Transcribing your answer…{" "}
                        <span
                          className="font-mono tabular-nums"
                          aria-live="polite"
                          data-testid="stt-transcribing-elapsed"
                        >
                          {Math.floor(transcribingElapsedSec / 60)}:
                          {String(transcribingElapsedSec % 60).padStart(2, "0")}
                        </span>
                        <span className="mt-2 block text-sm font-normal text-on-surface-variant/70">
                          {transcribingElapsedSec >= 60
                            ? "Almost there… your transcript will appear shortly."
                            : transcribingElapsedSec >= 30
                              ? "Still transcribing… AWS is taking longer than usual."
                              : "This usually takes 15-20 seconds."}
                        </span>
                      </>
                    ) : isRecording ? (
                      "Recording… tap the button again to stop and submit"
                    ) : (
                      "Tap the microphone to speak your answer"
                    )}
                  </p>

                  {isTranscribing && (
                    <div
                      className="mb-8 h-1 w-48 overflow-hidden rounded-full bg-surface-container-high"
                      role="progressbar"
                      aria-label="Transcribing your answer"
                    >
                      <div className="h-full w-1/3 animate-indeterminate-bar rounded-full bg-primary" />
                    </div>
                  )}

                  <div className="relative">
                    <div
                      className={`absolute -inset-4 rounded-full blur-xl ${
                        isRecording ? "bg-error/30" : "bg-primary/5"
                      }`}
                    ></div>
                    <button
                      type="button"
                      onClick={handleMicClick}
                      disabled={isSubmitting || isTranscribing}
                      aria-label={
                        isTranscribing
                          ? "Transcribing"
                          : isRecording
                            ? "Stop recording"
                            : "Start recording"
                      }
                      className={`relative flex h-24 w-24 items-center justify-center rounded-full text-on-primary shadow-lg transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 ${
                        isRecording
                          ? "animate-pulse bg-error hover:bg-error/90"
                          : "bg-primary hover:bg-primary-dim"
                      }`}
                    >
                      <span
                        className="material-symbols-outlined text-4xl"
                        data-weight="fill"
                        style={{ fontVariationSettings: '"FILL" 1' }}
                      >
                        {isTranscribing
                          ? "hourglass_top"
                          : isRecording
                            ? "stop"
                            : "mic"}
                      </span>
                    </button>
                  </div>

                  <div className="mt-8 flex gap-2">
                    <div
                      className={`h-4 w-1 rounded-full ${
                        isRecording ? "bg-error/40" : "bg-primary/20"
                      }`}
                    ></div>
                    <div
                      className={`h-8 w-1 rounded-full ${
                        isRecording ? "bg-error/60" : "bg-primary/40"
                      }`}
                    ></div>
                    <div
                      className={`h-12 w-1 rounded-full ${
                        isRecording ? "bg-error" : "bg-primary"
                      }`}
                    ></div>
                    <div
                      className={`h-6 w-1 rounded-full ${
                        isRecording ? "bg-error/70" : "bg-primary/60"
                      }`}
                    ></div>
                    <div
                      className={`h-10 w-1 rounded-full ${
                        isRecording ? "bg-error/80" : "bg-primary/80"
                      }`}
                    ></div>
                  </div>

                  {audioError && (
                    <p className="mt-6 max-w-md text-center text-sm text-error">
                      {audioError}
                    </p>
                  )}
                </div>

                {/*
                  Issue #71 — anti-cheat surface for the answer textarea.

                  Programmatic insertions (the transcript populated by
                  setTypedAnswer) bypass all of these handlers because
                  they aren't user input events, so the new flow keeps
                  working. The handlers only block USER paths:

                    - onCopy / onCut / onPaste:  clipboard via menus + keys
                    - onKeyDown:                 Ctrl/Cmd+C/V/X, Shift+Insert,
                                                 Ctrl+Insert, Shift+Delete
                    - onContextMenu:             right-click "Paste" menu
                    - onDrop / onDragOver:       drag-and-drop text/files
                    - onBeforeInput:             cross-browser InputEvent
                                                 belt-and-suspenders for
                                                 paths that bypass onPaste
                                                 (async Clipboard API,
                                                 some mobile keyboards,
                                                 undo-restore-of-paste)
                    - onChange rate limit:       blocks bulk insertion if
                                                 anything above slips through
                    - data-gramm* attrs:         disable Grammarly extension
                    - data-lt-active="false":    disable LanguageTool
                    - autoComplete + name="":    disable browser autofill
                    - autoCorrect / spellCheck:  disable native suggestions
                */}
                {/* [STT #72] Live streaming preview. Renders only when
                    the feature flag is on AND we either have a partial
                    in flight or we're actively streaming. The italic-
                    grey treatment signals "this text may still change"
                    so the student knows the textarea is the source of
                    truth. */}
                {STREAMING_ENABLED &&
                  (speech.status === "connecting" ||
                    speech.status === "streaming" ||
                    speech.status === "stopping" ||
                    speech.partial) && (
                    <div
                      className="mb-2 min-h-[2.5rem] rounded-xl border border-outline-variant/20 bg-surface-container px-3 py-2 font-body text-sm italic text-outline"
                      aria-live="polite"
                      data-testid="stt-partial-preview"
                    >
                      {speech.partial ||
                        (speech.status === "connecting"
                          ? "Connecting…"
                          : speech.status === "stopping"
                            ? "Finalising…"
                            : "Listening…")}
                    </div>
                  )}

                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-4 flex items-center">
                    <span className="material-symbols-outlined text-outline">
                      keyboard
                    </span>
                  </div>

                  <textarea
                    className="block w-full rounded-xl border border-outline-variant/20 bg-surface-container-lowest py-4 pl-12 pr-4 font-body text-sm placeholder:text-outline-variant focus:border-primary focus:ring-primary disabled:cursor-not-allowed disabled:opacity-60"
                    placeholder="Type your response here if you prefer not to use voice..."
                    rows="4"
                    value={typedAnswer}
                    onChange={(e) => {
                      const next = e.target.value;
                      if (next.length - typedAnswer.length > 5) return;
                      setTypedAnswer(next);
                    }}
                    disabled={audioBusy}
                    onCopy={(e) => e.preventDefault()}
                    onPaste={(e) => e.preventDefault()}
                    onCut={(e) => e.preventDefault()}
                    onBeforeInput={(e) => {
                      // Block insertions whose origin is paste or drop —
                      // catches paths that don't fire onPaste/onDrop on
                      // some browsers (Safari async Clipboard API, mobile
                      // long-press paste, undo of a prior paste).
                      const inputType = e.nativeEvent?.inputType || "";
                      if (
                        inputType === "insertFromPaste" ||
                        inputType === "insertFromPasteAsQuotation" ||
                        inputType === "insertFromDrop" ||
                        inputType === "insertFromYank"
                      ) {
                        e.preventDefault();
                      }
                    }}
                    onKeyDown={(e) => {
                      const key = e.key?.toLowerCase();
                      if (
                        (e.ctrlKey || e.metaKey) &&
                        ["c", "v", "x"].includes(key)
                      ) {
                        e.preventDefault();
                        return;
                      }
                      if (e.key === "Insert" && (e.shiftKey || e.ctrlKey)) {
                        e.preventDefault();
                        return;
                      }
                      if (e.key === "Delete" && e.shiftKey) {
                        e.preventDefault();
                      }
                    }}
                    onDrop={(e) => e.preventDefault()}
                    onDragOver={(e) => e.preventDefault()}
                    onContextMenu={(e) => e.preventDefault()}
                    name=""
                    autoComplete="off"
                    autoCorrect="off"
                    autoCapitalize="off"
                    spellCheck={false}
                    data-gramm="false"
                    data-gramm_editor="false"
                    data-enable-grammarly="false"
                    data-lt-active="false"
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
                  disabled={isSubmitting || audioBusy || !typedAnswer.trim()}
                >
                  {isSubmitting ? "Submitting..." : "Submit Answer"}

                  <span className="material-symbols-outlined text-sm">
                    send
                  </span>
                </button>
              )}

              {((canComplete && !currentQuestion) || timerExpired) && (
                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-secondary py-4 font-bold text-on-secondary shadow-sm transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
                  onClick={handleCompleteSession}
                  disabled={isSubmitting || audioBusy}
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
                  Instructor's Tip
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
