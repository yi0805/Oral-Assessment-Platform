function InstructorFeedback({ studentAssessmentResults }) {
  console.log(studentAssessmentResults);

  return (
    <section>
      <h3 className="mb-6 text-xl font-bold text-on-surface">
        Course Instructor Guidance
      </h3>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {studentAssessmentResults.map((result) => (
          <div
            className="relative overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-6 shadow-sm"
            key={result.assessment}
          >
            <div className="absolute right-0 top-0 -mr-16 -mt-16 h-32 w-32 rounded-full bg-primary/5"></div>
            <div className="mb-4 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container text-outline">
                <span className="material-symbols-outlined">person</span>
              </div>
              <div>
                <p className="text-sm font-bold text-on-surface">
                  {result.instructorName}
                </p>
                <p className="text-xs text-on-surface-variant">
                  {result.department}
                </p>
              </div>
            </div>
            <p className="text-sm italic leading-relaxed text-on-surface-variant">
              {result.feedback}
            </p>
            <div className="mt-4 flex items-center justify-between border-t border-surface-container pt-4"></div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default InstructorFeedback;
