import { useMemo, useState } from "react";
import styled from "styled-components";

import { useGradebook } from "../../hooks/useGradebook";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";
import Button from "../../ui/Button";
import Input from "../../ui/Input";

import InstructorCourseDashboard from "./InstructorCourseDashboard";

const TopBar = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-l);
  margin-bottom: var(--space-xl);
`;

const SearchWrap = styled.div`
  flex: 1;
  min-width: 200px;
  max-width: 420px;
  margin-left: auto;
`;

const CourseGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-xl);
`;

const CourseCard = styled.button`
  background: radial-gradient(
    ellipse at left top,
    #d2faf6,
    ${({ $color }) => $color} 45%
  );
`;

const CardPhoto = styled.div`
  height: 120px;
  background: ${({ $color }) => $color};
  border-radius: 12px 12px 0 0;
`;

const CardFooter = styled.div`
  padding: var(--space-m);
`;

const CourseName = styled.p`
  margin: 0;
  font-weight: 600;
  color: var(--color-primary);
`;

const AddCourseCard = styled.button`
  border: 2px dashed var(--color-light-2);
  border-radius: 12px;
  background: var(--color-primary-tint);
  min-height: 168px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-secondary);
  cursor: pointer;
  font: inherit;

  &:hover {
    border-color: var(--color-secondary);
    background: var(--color-secondary-tint);
  }

  &:focus-visible {
    outline: 2px solid var(--color-secondary);
    outline-offset: 2px;
  }
`;

const EmptyState = styled.p`
  margin-top: var(--space-l);
  color: var(--color-dark-2);
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

  const shownCourses = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return allCourses;

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

    setCourseCode("");
    setCourseName("");
    setCourseDesc("");
    setShowAddForm(false);
  }

  if (selectedCourse) {
    return (
      <ContentCard>
        <InstructorCourseDashboard
          key={selectedCourse.id}
          course={selectedCourse}
          onBack={() => setSelectedCourse(null)}
        />
      </ContentCard>
    );
  }

  return (
    // <ContentCard>
    //   <TopBar>
    //     <Heading $variant="page" style={{ marginBottom: 0 }}>
    //       My Courses
    //     </Heading>

    //     <SearchWrap>
    //       <SearchBar
    //         value={search}
    //         onChange={(e) => setSearch(e.target.value)}
    //         placeholder="Search by course code or name"
    //       />
    //     </SearchWrap>
    //   </TopBar>

    //   {showAddForm && (
    //     <AddPanel>
    //       <Heading
    //         as="h2"
    //         $variant="page"
    //         style={{
    //           fontSize: "var(--font-size-l)",
    //           marginBottom: "var(--space-m)",
    //         }}
    //       >
    //         Add Course
    //       </Heading>

    //       <form onSubmit={handleAddCourse}>
    //         <FormStack>
    //           <div>
    //             <FieldLabel htmlFor="new-course-code">Course code</FieldLabel>
    //             <Input
    //               id="new-course-code"
    //               value={courseCode}
    //               onChange={(e) => setCourseCode(e.target.value)}
    //               placeholder="e.g. COMPSCI 101"
    //               required
    //             />
    //           </div>

    //           <div>
    //             <FieldLabel htmlFor="new-course-name">Course name</FieldLabel>
    //             <Input
    //               id="new-course-name"
    //               value={courseName}
    //               onChange={(e) => setCourseName(e.target.value)}
    //               placeholder="e.g. Intro to CS"
    //               required
    //             />
    //           </div>

    //           <div>
    //             <FieldLabel htmlFor="new-course-desc">
    //               Description (optional)
    //             </FieldLabel>
    //             <Input
    //               id="new-course-desc"
    //               value={courseDesc}
    //               onChange={(e) => setCourseDesc(e.target.value)}
    //               placeholder="Short course description"
    //             />
    //           </div>
    //         </FormStack>

    //         <FormActions>
    //           <Button type="submit" $variant="primary">
    //             Add course
    //           </Button>
    //           <Button
    //             type="button"
    //             $variant="secondary"
    //             onClick={() => setShowAddForm(false)}
    //           >
    //             Cancel
    //           </Button>
    //         </FormActions>
    //       </form>
    //     </AddPanel>
    //   )}

    //   {shownCourses.length === 0 && <EmptyState>No courses found.</EmptyState>}

    //   <CourseGrid>
    //     {shownCourses.map((course) => (
    //       <CourseCard
    //         key={course.id}
    //         type="button"
    //         onClick={() => setSelectedCourse(course)}
    //       >
    //         <CardPhoto $color={course.color} />
    //         <CardFooter>
    //           <CourseName>{course.name}</CourseName>
    //         </CardFooter>
    //       </CourseCard>
    //     ))}

    //     <AddCourseCard
    //       type="button"
    //       onClick={() => setShowAddForm(true)}
    //       aria-label="Add course"
    //     >
    //       +
    //     </AddCourseCard>
    //   </CourseGrid>
    // </ContentCard>
    <>
    
    <main className="min-h-screen bg-surface pl-64 pt-24">
    
      <div className="mx-auto max-w-7xl px-10 pb-20">

        <header
          className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end"
        >
          <div>
            <span
              className="mb-2 block text-[11px] font-bold uppercase tracking-[0.2em] text-secondary"
              >Curator Dashboard</span
            >
            <h1
              className="font-headline text-4xl font-extrabold tracking-tight text-on-surface"
            >
              My Courses
            </h1>
            <p
              className="mt-2 max-w-xl font-body leading-relaxed text-on-surface-variant"
            >
              Manage your academic syllabus, track curriculum progress, and
              update course materials for the upcoming semester.
            </p>
          </div>
        </header>
        <div className="mb-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div
            className="rounded-xl border border-outline-variant/5 bg-surface-container-lowest p-6 shadow-sm"
          >
            <p
              className="mb-1 text-xs font-bold uppercase tracking-wider text-on-surface-variant"
            >
              Active Students
            </p>
            <p className="font-headline text-3xl font-bold text-primary">1,248</p>
          </div>
          <div
            className="rounded-xl border border-outline-variant/5 bg-surface-container-lowest p-6 shadow-sm"
          >
            <p
              className="mb-1 text-xs font-bold uppercase tracking-wider text-on-surface-variant"
            >
              Avg. Completion
            </p>
            <p className="font-headline text-3xl font-bold text-primary">84%</p>
          </div>
          <div
            className="rounded-xl border border-outline-variant/5 bg-surface-container-lowest p-6 shadow-sm"
          >
            <p
              className="mb-1 text-xs font-bold uppercase tracking-wider text-on-surface-variant"
            >
              Pending Reviews
            </p>
            <p className="font-headline text-3xl font-bold text-error">12</p>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {shownCourses.map((course) => (
          <button key={course.id} 
            className="group flex flex-col overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm transition-all duration-300 hover:shadow-xl hover:shadow-primary/5"
            onClick={() => setSelectedCourse(course)}
          >
            <div className="relative h-48 overflow-hidden bg-gradient-to-tl}">
              {/* <img
                alt="Introduction to Quantum Algorithms"
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                data-alt="abstract artistic visualization of quantum computing particles and glowing neural networks in shades of deep blue and silver"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDLbme1-qtM-UiAbbRFvXko7Ur40IJU1CBzy3M3WHfExnXfRas6WWB04oszNzkn0HIuIQqS95c0mvlebbnGtYYO7g1P_aKSA4_eo8JxtbzCni53M6QEMqFFm_Cpc4k4tR2VRuS2xq_JvfHWyyfbOBdKJBFovrjTHxTlBWnp9o3X5dVGN3QIXrgZ5KbGFEuLn6l13JL7-rYWoW4OA7lvh9w9C30C_hUWpOKEnJV6A-_tyaYBGPQn9-PchQud7QYn1QVyWuVaXBoY9VFk"
              /> */}
              <div
                className="absolute right-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-primary backdrop-blur-md"
              >
                Active
              </div>
            </div>
            <div className="flex flex-grow flex-col p-6">
              <span className="mb-1 font-body text-xs font-bold text-secondary-dim"
                >{course.code}</span
              >
              <h3
                className="mb-3 font-headline text-xl font-bold text-on-surface transition-colors group-hover:text-primary"
              >
                {course.name}
              </h3>
              <p
                className="mb-6 flex-grow font-body text-sm leading-relaxed text-on-surface-variant"
              >
                {course.description}
              </p>
              <div
                className="flex items-center justify-between border-t border-outline-variant/10 pt-6"
              >
                
                {/* <button
                  className="group/btn flex items-center gap-1 text-sm font-bold text-primary hover:underline"
                >
                  Manage Course
                  <span
                    className="material-symbols-outlined text-sm transition-transform group-hover/btn:translate-x-1"
                    >arrow_forward</span
                  >
                </button> */}
              </div>
            </div>
          </button>
          ))}
          
        </div>
      </div>
    </main>
    <div className="fixed bottom-8 right-8 z-50">
      <button
        className="group flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-on-primary shadow-2xl transition-all hover:bg-primary-dim active:scale-90"
      >
        <span
          className="material-symbols-outlined text-3xl transition-transform duration-300 group-hover:rotate-90"
          >add</span
        >
      </button>
    </div>
    </>
  );
}

export default InstructorHome;

