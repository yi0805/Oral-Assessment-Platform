import { useNavigate } from "react-router";

import { useGradebook } from "../../hooks/useGradebook";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";
import Button from "../../ui/Button";
import Input from "../../ui/Input";

import InstructorCourseDashboard from "./InstructorCourseDashboard";
import getInstructorByName from "../../utils/getInstructorByname";
import getUngradedAssessmentsByInstructor from "../../utils/getUngradedAssessmentsByInstructor";
import InstructorCourseCard from "../../ui/InstructorCourseCard";
import getCourseInfoByInstructor from "../../utils/getCourseInfoByInstructor";

const SearchWrap = styled.div`
  flex: 1;
  width: 350px;
  max-width: 420px;
  margin-left: auto;
  float: right;
`;

const FormStack = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
  margin-top: var(--space-l);
  max-width: 40ch;
`;

const FormActions = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-m);
  margin-top: var(--space-m);
`;

const AddPanel = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
  background: var(--color-primary-tint);
`;

const FieldLabel = styled.label`
  display: block;
  font-size: var(--font-size-s);
  color: var(--color-dark-2);
  margin-bottom: var(--space-xs);
`;

function InstructorHome() {
  const { allCourses, addCourse } = useGradebook();
  const [search, setSearch] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [courseCode, setCourseCode] = useState("");
  const [courseName, setCourseName] = useState("");
  const [courseDesc, setCourseDesc] = useState("");
  
  
  const images = [
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDfgr_pP5i7hQoboiS_DsxFRPWBpPHlHpUXumClpddDt2JX7BsTy1RucSS9hAnXPHskftAHFN-qV7kXv61MwoKaNkxvqx41RxJsHnItt2OmhV9TcIGhNkjwwWJDIJBpGx1OVaevsdmzLdL53qdnBksk7Ks2vMWDlbrBRf0JdHg25PrboJ2OYXhx8vTxAta6zZTLt7dT2JXlzV-OxVl6RPR0-L5aXHJxzBKh-c8MTw86BqkmHDoPdgqjbfQS5aA-OmT8pNhuXzlc9KnW",
      "https://lh3.googleusercontent.com/aida-public/AB6AXuB_TjDjVsjnTlwmwB0gDWQ-U-AahXp_b8lpZ14Py7eMk63zOzkUqUQY-fl84SbQNLlfXPTSiOIRYU2xEJifhcY4N89ZTCr_TgabEFJOIB3cWQ6Z3jbHwc1PgxOq1jlbQ8iDTpIqVZygzlUnDqyjLMls7D0mxC5SVAM72ouBfbQxbsry7nnfEvvz4N_98td94vnn2IeNKd1h7VtcH-K_2IxLA3Oyj9lJSAjpyhlIt1Q2PNLzsuWcShb3aU5ul55WCaN6KbiRdFrrKkwr",
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBkdEcmqThK9dB3ArCqjwxvzz0_opItvI_4i5g5B7fE9L9qJWK4DObWAy-H_so9vgD-23qb2yHLjtLT9BFh8XFyu04NVBfRxEjOqvlsjG3M9Tp-oMfFMp3zlWeSnECBfU5vCdos9eKFWh-_NoPZekYd2X7W54Bx7_PW4XYDBzoIZO3qPpmkeTUlMHXH2wQV1sjNGM9M4JUfQFKSxVpQ4edkqmDEPnWfGhBSdPhq-DcrNyUu3HFuMvugK6n5-f_mGHhyk5M-V3F7jXAS",
      "https://lh3.googleusercontent.com/aida-public/AB6AXuD3shRtSi9buB-3A-lLTQ-XDY7NQG2J-VCj0tz2hARiNzaRoOFQrXO9Wl68MzBMooDvHYVyHO_AFPzg-dzGNVkNiWxfHaCW5dK13_iHPu2I1ShEejxdAYAe4Jnmr4FWg-mgmZKoifN0QGfj5cBQNLdYT2deMzRZY2xM_a-Y8SbUmZHORRYEYRhk9R6f0TbxWHcn4IZ0YmXGfhHXADRdSOMKeCtdWd57cobtYtdTZKLkprfY_hZlHhTroGscGQlV6tj67fIz5x3pPsoA",
    ];
  
  const shownCourses = useMemo(() => {
    const value = search.trim().toLowerCase();
    
    if (!value) return allCourses;
    console.log(course.code);
    
    return allCourses.filter(
      (course) =>
        course.code.toLowerCase().includes(value) ||
      course.name.toLowerCase().includes(value) ||
      (course.description &&
        course.description.toLowerCase().includes(value)),
      );
  }, [allCourses, search]);

  function handleAddCourse(e) {
    e.preventDefault();

    if (!courseCode.trim() || !courseName.trim()) return;

    addCourse({
      code: courseCode,
      name: courseName,
      description: courseDesc,
    });
  const navigate = useNavigate();

  const Username = localStorage.getItem("userName");
  const instructor = getInstructorByName(Username);
  const courses = getCourseInfoByInstructor(instructor);

  const unGradedAssessments = getUngradedAssessmentsByInstructor(instructor);

  return (
    <>
      <main className="min-h-screen bg-surface pl-64 pt-24">
        <div className="mx-auto max-w-7xl px-10 pb-20">
          <header className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div>
              <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
                My Courses
              </h1>
            </div>
          </header>

          <div className="mb-10">
            <div className="flex flex-col items-center justify-between gap-6 rounded-xl border border-outline-variant/10 bg-surface-container-lowest p-5 shadow-sm md:flex-row md:p-6">
              <div className="flex items-center gap-6">
                <div className="flex flex-col">
                  <div className="mb-1 flex items-center gap-2">
                    <span className="material-symbols-outlined text-lg text-error">
                      assignment_late
                    </span>
                    <span className="font-headline text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                      Pending Reviews
                    </span>
                  </div>
                  <h2 className="text-center font-headline text-4xl font-extrabold leading-none tracking-tight text-primary">
                    {unGradedAssessments.length}
                  </h2>
                </div>
                <div className="hidden h-10 w-[1px] bg-outline-variant/20 md:block"></div>
                <p className="max-w-sm font-body text-sm text-on-surface-variant">
                  Student submissions are currently awaiting your feedback and
                  grading.
                </p>
              </div>
              <div className="flex w-full flex-row gap-3 md:w-auto">
                <button
                  className="flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2 font-headline text-xs font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-95"
                  onClick={() => {
                    navigate("/instructor/pendingGrades", {
                      state: {
                        unGradedAssessments,
                      },
                    });
                  }}
                >
                  Review Submissions
                  <span className="material-symbols-outlined text-xs">
                    arrow_forward
                  </span>
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            <InstructorCourseCard courses={courses} />
          </div>
        </div>
      </main>
      <div className="fixed bottom-8 right-8 z-50">
        <button className="group flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-on-primary shadow-2xl transition-all hover:bg-primary-dim active:scale-90">
          <span className="material-symbols-outlined text-3xl transition-transform duration-300 group-hover:rotate-90">
            add
          </span>
        </button>
      </div>
    </>
  );
}
}
export default InstructorHome;
