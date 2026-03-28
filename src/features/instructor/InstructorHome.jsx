import { useMemo, useState } from "react";
import styled from "styled-components";

import { useGradebook } from "../../hooks/useGradebook";
import ContentCard from "../../ui/ContentCard";

import InstructorCourseDashboard from "./InstructorCourseDashboard";

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
    <>
      <main className="min-h-screen bg-surface pl-64 pt-24">
        <div className="mx-auto max-w-7xl px-10 pb-20">
          <header className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div>
              <span className="mb-2 block text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
                Dashboard
              </span>
              <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
                My Courses
              </h1>
              <p className="mt-2 max-w-xl font-body leading-relaxed text-on-surface-variant">
                Manage your academic syllabus, track curriculum progress, and
                update course materials for the upcoming semester.
              </p>
            </div>
          </header>

          <div className="mb-16 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-xl border border-outline-variant/5 bg-surface-container-lowest p-6 shadow-sm">
              <p className="mb-1 text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                Pending Reviews
              </p>
              <p className="font-headline text-3xl font-bold text-error">12</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {shownCourses.map((course, index) => (
              <button
                key={course.id}
                className="group flex flex-col overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest shadow-sm transition-all duration-300 hover:shadow-xl hover:shadow-primary/5"
                onClick={() => setSelectedCourse(course)}
              >
                <div className="bg-gradient-to-tl} relative h-48 overflow-hidden">
                  <img
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    data-alt="abstract artistic visualization of quantum computing particles and glowing neural networks in shades of deep blue and silver"
                    src={images[index % images.length]}
                  />
                  <div className="absolute right-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-primary backdrop-blur-md">
                    Active
                  </div>
                </div>
                <div className="flex flex-grow flex-col p-6">
                  <span className="mb-1 font-body text-xs font-bold text-secondary-dim">
                    {course.code}
                  </span>
                  <h3 className="mb-3 font-headline text-xl font-bold text-on-surface transition-colors group-hover:text-primary">
                    {course.name}
                  </h3>
                  <p className="mb-6 flex-grow font-body text-sm leading-relaxed text-on-surface-variant">
                    {course.description}
                  </p>
                  {/* <div
                className="flex items-center justify-between border-t border-outline-variant/10 pt-6"
              >                
                <button
                  className="group/btn flex items-center gap-1 text-sm font-bold text-primary hover:underline"
                >
                  Manage Course
                  <span
                    className="material-symbols-outlined text-sm transition-transform group-hover/btn:translate-x-1"
                    >arrow_forward</span
                  >
                </button>
              </div> */}
                </div>
              </button>
            ))}
            <div className="group flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed border-outline-variant/30 p-8 text-center transition-all duration-300 hover:border-primary/50 hover:bg-primary-container/10">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-container transition-all group-hover:bg-primary group-hover:text-on-primary">
                <span className="material-symbols-outlined text-3xl">add</span>
              </div>
              <h3 className="font-headline text-lg font-bold text-on-surface">
                Initialize New Course
              </h3>
              <p className="mt-2 font-body text-sm text-on-surface-variant">
                Create a new academic syllabus and invite teaching assistants.
              </p>
            </div>
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

export default InstructorHome;
