import getInstructorByName from "../../utils/getInstructorByname";
import getCoursesByInstructor from "../../utils/getCoursesByInstructor";

function UpdateMaterial() {
  // const Username = localStorage.getItem("userName");
  // const instructor = getInstructorByName(Username);
  // const courses = getCoursesByInstructor(instructor);

  return (
    <div className="min-h-screen">
      <main className="ml-64 min-h-screen pt-16">
        <div className="mx-auto max-w-6xl px-8 py-12">
          <div className="mb-10">
            <h1 className="text-4xl font-extrabold tracking-tight text-on-background">
              Update Material
            </h1>
          </div>

          <div className="grid grid-cols-12 items-start gap-6">
            <div className="col-span-12 space-y-6 lg:col-span-5">
              <section className="h-full rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
                <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
                  <span
                    className="material-symbols-outlined text-primary"
                    data-icon="description"
                    style={{ verticalAlign: "middle" }}
                  >
                    description
                  </span>
                  Assessment Parameters
                </h2>

                <form className="space-y-6">
                  <div className="space-y-2">
                    <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                      Select Course
                    </label>
                    <div className="group relative">
                      <select className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20">
                        {/* {courses.map((course) => (
                          <option key={course.id}>{course.id}</option>
                        ))} */}
                      </select>
                      <span
                        className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
                        data-icon="expand_more"
                        style={{ verticalAlign: "middle" }}
                      >
                        expand_more
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                      Assessment Name
                    </label>
                    <input
                      className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                      placeholder="e.g. Intro to Python"
                      type="text"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                      Number of Questions
                    </label>
                    <input
                      className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                      max="100"
                      min="1"
                      placeholder="e.g., 20"
                      type="number"
                    />
                  </div>
                </form>
              </section>
            </div>

            <div className="col-span-12 space-y-6 lg:col-span-7">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <section className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-6 text-center">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
                    <span
                      className="material-symbols-outlined text-2xl text-primary"
                      data-icon="upload_file"
                      style={{ verticalAlign: "middle" }}
                    >
                      upload_file
                    </span>
                  </div>
                  <h3 className="mb-1 text-base font-bold">Assessment PDF</h3>
                  <p className="mb-4 px-2 text-[11px] text-on-surface-variant">
                    Upload the source material or a previous assessment to
                    refine your questions.
                  </p>

                  <div className="w-full space-y-3">
                    <div className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-3 text-left shadow-sm">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-error/10 text-error">
                        <span
                          className="material-symbols-outlined text-xl"
                          data-icon="picture_as_pdf"
                          style={{ verticalAlign: "middle" }}
                        >
                          picture_as_pdf
                        </span>
                      </div>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold">
                          Curriculum_2024_Final.pdf
                        </p>
                        <p className="text-[9px] text-outline">
                          2.4 MB • Ready
                        </p>
                      </div>
                      <button className="text-on-surface-variant transition-colors hover:text-error">
                        <span
                          className="material-symbols-outlined text-lg"
                          data-icon="close"
                          style={{ verticalAlign: "middle" }}
                        >
                          close
                        </span>
                      </button>
                    </div>

                    <label className="block cursor-pointer">
                      <input className="hidden" type="file" accept=".pdf" />
                      <div className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                        Browse Files
                      </div>
                    </label>
                  </div>
                </section>

                <section className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-6 text-center">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm">
                    <span
                      className="material-symbols-outlined text-2xl text-secondary"
                      data-icon="rule"
                      style={{ verticalAlign: "middle" }}
                    >
                      rule
                    </span>
                  </div>
                  <h3 className="mb-1 text-base font-bold">
                    Assessment Rubrics
                  </h3>
                  <p className="mb-4 px-2 text-[11px] text-on-surface-variant">
                    Upload evaluation criteria for precise grading.
                  </p>
                  <div className="w-full space-y-3">
                    <label className="block cursor-pointer">
                      <input className="hidden" type="file" accept=".pdf" />
                      <div className="group flex w-full flex-col items-center gap-1 rounded-xl border-2 border-dashed border-outline-variant/10 bg-surface-container-lowest/50 py-6 transition-all hover:border-primary/20 hover:bg-white">
                        <span
                          className="material-symbols-outlined text-xl text-outline transition-colors group-hover:text-primary"
                          data-icon="add_circle"
                          style={{ verticalAlign: "middle" }}
                        >
                          add_circle
                        </span>
                        <span className="text-[10px] font-medium text-on-surface-variant transition-colors group-hover:text-primary">
                          Drop rubrics here
                        </span>
                      </div>
                    </label>
                    <label className="block cursor-pointer">
                      <input className="hidden" type="file" accept=".pdf" />
                      <div className="w-full rounded-xl border border-outline-variant/20 bg-white py-2.5 text-center text-xs font-bold text-primary transition-all hover:bg-primary/5">
                        Browse Files
                      </div>
                    </label>
                  </div>
                </section>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-primary/10 bg-primary/5 p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-primary/10 p-3 text-primary">
                    <span
                      className="material-symbols-outlined"
                      data-icon="auto_awesome"
                      style={{ verticalAlign: "middle" }}
                    >
                      auto_awesome
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-bold text-primary">
                      AI Question Generation
                    </p>
                    <p className="text-[11px] text-on-surface-variant">
                      Update questions based on material
                    </p>
                  </div>
                </div>
                <button className="rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]">
                  Update Now
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-12 gap-6">
            <div className="col-span-12">
              <div className="flex h-full items-center gap-6 rounded-xl bg-surface-container p-6">
                <img
                  alt="AI Assistant Placeholder"
                  className="h-12 w-12 rounded-lg object-cover opacity-60 grayscale"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuDVCGVyyQqfO-19vp2pmD6AID9Ui4jZyVdFBJC4Dd9xIwyi_Wq3zmfIrzALaNCanKTKzb69Zw80EoWXyNplx9aPxwuzrUKam9awbyqcrNcNnR607gF_8jVGD_WYOsOIV3Ykxl4NHG7Tk3vrvrnqBcQZ7wnwI3tZRmk2UYvJtFtsfSxcI5ynho1SQgebXGpy91RN9qpxIAh6BVWjZf3s_99wKYtTr9KAPOWeND0i8Rn0e2imsnCp5pNpUGQw_mXdGzzUlxtInB2-xVVj"
                />
                <div className="flex-1">
                  <h4 className="text-sm font-bold text-on-surface">
                    Curator's Tip
                  </h4>
                  <p className="text-xs leading-relaxed text-on-surface-variant">
                    Ensure clear headings and objectives for 30% faster AI
                    results with OCR-processed documents.
                  </p>
                </div>
                <button className="shrink-0 rounded-lg px-4 py-2 text-xs font-bold text-primary transition-all hover:bg-white">
                  View Guide
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default UpdateMaterial;
