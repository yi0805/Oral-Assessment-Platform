import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router";

import { useMoveBack } from "../../hooks/useMoveBack";
import { useTranscript } from "./useTranscript";
import Spinner from "../../ui/Spinner";
import { buildQuestionBlocks } from "../../utils/buildQuestionBlocks";
import { useUpdateReview } from "./useUpdateReview";

function Transcipt() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [finalGrade, setFinalGrade] = useState("");
  const [comments, setComments] = useState("");

  const moveback = useMoveBack();
  const { transcript, isLoading } = useTranscript(sessionId);
  const { updateReview } = useUpdateReview();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    if (!transcript) return;

    setFinalGrade(transcript.instructor_feedback?.final_grade ?? "");
    setComments(transcript.instructor_feedback?.comments ?? "");
  }, [transcript]);

  useEffect(() => {
    setCurrentIndex(0);
  }, [sessionId]);

  if (isLoading) return <Spinner />;

  const reviews = location.state?.reviews || [];
  const currentReviewIndex = location.state?.currentReviewIndex ?? -1;

  const questionBlocks = buildQuestionBlocks(transcript.transcript) || [];
  const block = questionBlocks[currentIndex];

  console.log(transcript);
  console.log(questionBlocks);
  console.log(block);

  function handlePrevStudent() {
    if (currentReviewIndex <= 0) return;

    const prevReview = reviews[currentReviewIndex - 1];

    navigate(`/instructor/transcript/${prevReview.sessionId}`, {
      state: {
        reviews,
        currentReviewIndex: currentReviewIndex - 1,
      },
    });
  }

  function handleNextStudent() {
    if (currentReviewIndex >= reviews.length - 1) return;

    const nextReview = reviews[currentReviewIndex + 1];

    navigate(`/instructor/transcript/${nextReview.sessionId}`, {
      state: {
        reviews,
        currentReviewIndex: currentReviewIndex + 1,
      },
    });
  }

  function handleSubmitReview() {
    if (finalGrade === "") return;

    updateReview({
      sessionId,
      finalGrade: Number(finalGrade),
      comments: comments,
    });
  }

  return (
    <div className="font-body">
      <main className="min-h-screen pl-64 pt-16">
        <div className="mx-auto max-w-6xl px-12 py-16">
          <button
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
            onClick={moveback}
          >
            <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>
            <span className="font-body uppercase tracking-widest">
              Back to Dashboard
            </span>
          </button>
          <div className="mb-12">
            <div className="flex items-end justify-between">
              <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
                Student Response Detail
              </h1>

              <div className="flex gap-3">
                <button
                  className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container disabled:opacity-40"
                  onClick={handlePrevStudent}
                  disabled={currentReviewIndex <= 0}
                >
                  Previous
                </button>
                <button
                  className="rounded-xl px-5 py-2 text-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container disabled:opacity-40"
                  onClick={handleNextStudent}
                  disabled={
                    currentReviewIndex === -1 ||
                    currentReviewIndex >= reviews.length - 1
                  }
                >
                  Next Student
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-12 gap-8">
            <div className="col-span-12 flex flex-col gap-8 lg:col-span-4">
              <div className="rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-8">
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 h-24 w-24 rounded-full border-2 border-primary-container p-1">
                    <img
                      alt="Student avatar"
                      className="h-full w-full rounded-full object-cover"
                      src={transcript.student.image || "/WhereRU.png"}
                    />
                  </div>
                  <h2 className="font-headline text-xl font-bold text-on-surface">
                    {transcript.student.full_name || "Known Student"}
                  </h2>
                  <p className="mb-4 text-sm text-outline">
                    {transcript.assessment.title || "Unknown Assessment"}
                  </p>

                  <div className="flex gap-2">
                    <span className="rounded-full bg-tertiary-container px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-on-tertiary-container">
                      Active Enrollment
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-primary/10 bg-primary-container p-8">
                <div className="mb-2 flex items-start justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-widest text-on-primary-container">
                    Score
                  </span>
                  <span className="material-symbols-outlined text-on-primary-container opacity-50">
                    auto_awesome
                  </span>
                </div>

                <div className="flex items-baseline gap-1">
                  <span className="font-headline text-5xl font-extrabold tracking-tighter text-on-primary-container">
                    {transcript.ai_summary.suggested_grade || "Unknown grade"}
                  </span>
                  <span className="text-lg font-bold text-on-primary-container opacity-60">
                    /10
                  </span>
                </div>
                <p className="mt-4 text-xs font-medium leading-snug text-on-primary-container">
                  {transcript.ai_summary.summary_text ||
                    "No AI summary available for this response."}
                </p>
              </div>
            </div>

            <div className="col-span-12 flex flex-col gap-6 lg:col-span-8">
              <div className="flex items-center justify-between rounded-xl border border-outline-variant/10 bg-surface-container-lowest px-6 py-4 shadow-sm">
                <div className="flex items-center gap-4">
                  <button
                    className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim disabled:cursor-not-allowed disabled:opacity-30"
                    onClick={() => setCurrentIndex((prev) => prev - 1)}
                    disabled={questionBlocks.length === 0 || currentIndex <= 0}
                  >
                    <span className="material-symbols-outlined text-base">
                      chevron_left
                    </span>
                    PREVIOUS
                  </button>
                  <span className="h-4 w-[1px] bg-outline-variant/30"></span>
                  <button
                    className="flex items-center gap-1 text-sm font-bold text-primary hover:text-primary-dim disabled:cursor-not-allowed disabled:opacity-30"
                    onClick={() => setCurrentIndex((prev) => prev + 1)}
                    disabled={
                      questionBlocks.length === 0 ||
                      currentIndex >= questionBlocks.length - 1
                    }
                  >
                    NEXT
                    <span className="material-symbols-outlined text-base">
                      chevron_right
                    </span>
                  </button>
                </div>

                <span className="text-[11px] font-bold uppercase tracking-widest text-outline">
                  Question {currentIndex + 1} of
                  {questionBlocks.length}
                </span>
              </div>

              <div className="space-y-6">
                {block && (
                  <div className="group">
                    <div className="mb-6 flex items-start gap-4">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container font-headline font-bold text-primary">
                        1
                      </span>

                      <div className="pt-1.5">
                        <h3 className="mb-2 font-headline text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                          Main Question
                        </h3>
                        <p className="font-body text-lg font-medium leading-relaxed text-on-surface">
                          {block.question}
                        </p>
                      </div>
                    </div>

                    <div className="ml-14 overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm">
                      <div className="flex items-center justify-between border-b border-outline-variant/10 bg-surface-container-low px-8 py-4">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-sm text-secondary">
                            subject
                          </span>
                          <span className="text-[11px] font-bold uppercase tracking-widest text-outline">
                            Student Response Transcript
                          </span>
                        </div>
                      </div>

                      <div className="space-y-6 p-8">
                        <p className="text-sm leading-relaxed text-on-surface">
                          {block.answer || "No answer yet"}
                        </p>

                        {block.followups.length > 0 && (
                          <div className="space-y-4 border-t border-outline-variant/10 pt-6">
                            {block.followups.map((followup, followupIndex) => (
                              <div
                                key={followup.sequenceNo}
                                className="space-y-2"
                              >
                                <h4 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                                  Follow-up {followupIndex + 1}
                                </h4>

                                <p className="text-sm font-medium leading-relaxed text-on-surface">
                                  {followup.question}
                                </p>

                                <p className="text-sm leading-relaxed text-on-surface-variant">
                                  {followup.answer || "No answer yet"}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 rounded-xl border-2 border-primary/20 bg-surface-container-lowest p-8 shadow-xl">
                <h3 className="mb-6 font-headline text-xl font-bold text-on-surface">
                  Instructor Review
                </h3>
                <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                  <div className="space-y-4 md:col-span-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-outline">
                      Final Assessment Comments
                    </label>
                    <textarea
                      className="h-32 w-full rounded-xl border-outline-variant/30 bg-surface-container-low p-4 font-body text-sm placeholder:text-outline/50 focus:border-primary focus:ring-0"
                      value={comments}
                      onChange={(e) => setComments(e.target.value)}
                      placeholder="Provide qualitative feedback..."
                    ></textarea>
                  </div>

                  <div className="flex flex-col gap-6">
                    <div>
                      <label className="mb-2 block text-xs font-bold uppercase tracking-widest text-outline">
                        Final Score
                      </label>

                      <div className="flex items-center gap-3">
                        <input
                          className="w-24 border-b-2 border-primary bg-transparent font-headline text-3xl font-extrabold text-primary focus:outline-none"
                          type="number"
                          min="0"
                          max="100"
                          value={finalGrade}
                          onChange={(e) => setFinalGrade(e.target.value)}
                        />

                        <span className="text-lg font-bold text-outline">
                          / 10
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <button
                        className="w-full rounded-xl bg-primary py-4 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]"
                        onClick={handleSubmitReview}
                      >
                        Confirm &amp; Submit Grade
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="h-16"></div>
        </div>
      </main>
    </div>
  );
}

export default Transcipt;
