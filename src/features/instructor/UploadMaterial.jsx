import getInstructorByName from "../../utils/getInstructorByname";
import mockCourses from "../../data/mockCourses";
import mockInstructor from "../../data/mockInstructor";
import getCourseInfoByInstructor from "../../utils/getCourseInfoByInstructor";


function UpdateMaterial(){
    const Username = localStorage.getItem("username");
    const instructor = getInstructorByName(Username);
    console.log(instructor.name);
    const courses = getCourseInfoByInstructor(instructor);
    console.log(courses);
    
return (
    <>
    <main className="min-h-screen pt-16">
        <div className="mx-auto max-w-5xl px-12 py-16">
            <div className="mb-12">
            <h1 className="text-4xl font-extrabold tracking-tight text-on-background">
                Update Material
            </h1>
            </div>
            <div className="grid grid-cols-12 gap-8">
                <div className="col-span-12 space-y-8 lg:col-span-7">
                    <section
                    className="rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]"
                    >
                    <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
                        <span
                        className="material-symbols-outlined text-primary"
                        data-icon="description"
                        >description</span
                        >
                        Assessment Parameters
                    </h2>
                    <form className="space-y-6">
                        <div className="space-y-2">
                        <label
                            className="ml-1 block text-sm font-semibold text-on-surface-variant"
                            >Select Course</label>
                        <div className="group relative">
                            <select
                            className="w-full cursor-pointer appearance-none rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20"
                            >
                            <option>{courses[0]}</option>
                            <option>{courses[1]}</option>
                            <option>{courses[2]}</option>
                            <option>{courses[3]}</option>
                            
                            </select>
                            <span
                            className="material-symbols-outlined pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant"
                            data-icon="expand_more"
                            >expand_more</span
                            >
                        </div>
                        </div>
                        <div className="space-y-2">
                        <label
                            className="ml-1 block text-sm font-semibold text-on-surface-variant"
                            >Assessment Name</label
                        >
                        <input
                            className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                            placeholder="e.g., Mid-Term Syllabus Update 2024"
                            type="text"
                        />
                        </div>
                        <div className="space-y-2">
                        <label
                            className="ml-1 block text-sm font-semibold text-on-surface-variant"
                            >Target Difficulty</label
                        >
                        <div className="grid grid-cols-3 gap-4">
                            <button
                            className="rounded-xl border-2 border-primary-container bg-primary-container/30 px-4 py-3 text-sm font-semibold text-primary transition-all hover:bg-primary-container/50"
                            type="button"
                            >
                            Foundational
                            </button>
                            <button
                            className="rounded-xl border-2 border-transparent bg-surface-container-low px-4 py-3 text-sm font-semibold text-on-surface-variant transition-all hover:bg-surface-container-high"
                            type="button"
                            >
                            Intermediate
                            </button>
                            <button
                            className="rounded-xl border-2 border-transparent bg-surface-container-low px-4 py-3 text-sm font-semibold text-on-surface-variant transition-all hover:bg-surface-container-high"
                            type="button"
                            >
                            Advanced
                            </button>
                        </div>
                        </div>
                        <div className="space-y-2">
                        <label
                            className="ml-1 block text-sm font-semibold text-on-surface-variant"
                            >Number of Questions</label
                        >
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
                    <div
                    className="flex items-center justify-between rounded-xl border border-primary/10 bg-primary/5 p-8"
                    >
                    <div className="flex items-center gap-4">
                        <div className="rounded-lg bg-primary/10 p-3 text-primary">
                        <span
                            className="material-symbols-outlined"
                            data-icon="auto_awesome"
                            >auto_awesome</span
                        >
                        </div>
                        <div>
                        <p className="font-bold text-primary">AI Question Generation</p>
                        <p className="text-xs text-on-surface-variant">
                            Update questions based on new material
                        </p>
                        </div>
                    </div>
                    <button
                        className="rounded-xl bg-primary px-8 py-4 font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98]"
                    >
                        Update Now
                    </button>
                    </div>
                </div>
            <div className="col-span-12 lg:col-span-5">
                <section
                className="flex h-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-8 text-center"
                >
                <div
                    className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-lowest shadow-sm"
                >
                    <span
                    className="material-symbols-outlined text-4xl text-primary"
                    data-icon="upload_file"
                    >upload_file</span
                    >
                </div>
                <h3 className="mb-2 text-xl font-bold">Assessment PDF</h3>
                <p className="mb-8 px-4 text-sm text-on-surface-variant">
                    Upload the source material or a previous assessment to refine
                    your questions.
                </p>
                <div className="w-full space-y-4">
                    <div
                    className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-4 text-left shadow-sm"
                    >
                    <div
                        className="flex h-10 w-10 items-center justify-center rounded bg-error/10 text-error"
                    >
                        <span
                        className="material-symbols-outlined"
                        data-icon="picture_as_pdf"
                        >picture_as_pdf</span
                        >
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold">
                        Curriculum_2024_Final.pdf
                        </p>
                        <p className="text-xs text-outline">2.4 MB • Ready</p>
                    </div>
                    <button
                        className="text-on-surface-variant transition-colors hover:text-error"
                    >
                        <span className="material-symbols-outlined" data-icon="close"
                        >close</span
                        >
                    </button>
                    </div>
                    <label className="block cursor-pointer">
                    <input className="hidden" type="file" />
                    <div
                        className="w-full rounded-xl border border-outline-variant/20 bg-white py-4 text-center text-sm font-bold text-primary transition-all hover:bg-primary/5"
                    >
                        Browse Other Files
                    </div>
                    </label>
                </div>
                <div className="mt-12 w-full border-t border-outline-variant/20 pt-8">
                    <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-on-surface-variant"
                        >Institutional Storage</span
                    >
                    <span className="text-xs font-bold text-primary">82% Full</span>
                    </div>
                    <div
                    className="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-highest"
                    >
                    <div className="h-full w-[82%] rounded-full bg-primary"></div>
                    </div>
                </div>
                </section>
            </div>
            </div>
            <div
            className="mt-12 flex items-center gap-6 rounded-xl bg-surface-container p-6"
            >
            <img
                alt="AI Assistant Placeholder"
                className="h-16 w-16 rounded-lg object-cover opacity-60 grayscale"
                data-alt="abstract tech texture with soft blue and teal lights, minimalist clean digital background"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDVCGVyyQqfO-19vp2pmD6AID9Ui4jZyVdFBJC4Dd9xIwyi_Wq3zmfIrzALaNCanKTKzb69Zw80EoWXyNplx9aPxwuzrUKam9awbyqcrNcNnR607gF_8jVGD_WYOsOIV3Ykxl4NHG7Tk3vrvrnqBcQZ7wnwI3tZRmk2UYvJtFtsfSxcI5ynho1SQgebXGpy91RN9qpxIAh6BVWjZf3s_99wKYtTr9KAPOWeND0i8Rn0e2imsnCp5pNpUGQw_mXdGzzUlxtInB2-xVVj"
            />
            <div className="flex-1">
                <h4 className="text-sm font-bold text-on-surface">Curator's Tip</h4>
                <p className="text-sm leading-relaxed text-on-surface-variant">
                For better AI generation results, ensure the PDF contains clear
                headings and structured learning objectives. The engine performs
                30% faster with OCR-processed documents.
                </p>
            </div>
            <button
                className="rounded-lg px-4 py-2 text-sm font-bold text-primary transition-all hover:bg-white"
            >
                View Guide
            </button>
            </div>
        </div>
    </main>
    </>
    );
}

export default UpdateMaterial;