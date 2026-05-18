import { useState } from "react";

import { useCourses } from "../../hooks/useCourses";
import { useUser } from "../authentication/useUser";

import SearchCouse from "../../ui/SearchCouse";
import CourseCard from "../../ui/CourseCard";
import Spinner from "../../ui/Spinner";

export default function StudentHome() {
  const [search, setSearch] = useState("");

  const { user, isLoading: isUserLoading } = useUser();
  const { courses, isLoading } = useCourses();

  if (isLoading || isUserLoading) return <Spinner />;

  const filteredCouses = courses.filter((course) =>
    course.course_code.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <main className="min-h-screen pt-16">
      <div className="mx-auto max-w-7xl px-8 py-12">
        <div className="mb-12">
          <h1 className="headline-font text-4xl font-extrabold tracking-tight text-on-surface">
            My Courses
          </h1>
        </div>

        <div className="mb-16 grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="relative overflow-hidden rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)] lg:col-span-8">
            <div className="relative z-10 flex h-full flex-col justify-center">
              <h2 className="headline-font mb-3 text-2xl font-bold text-primary">
                Welcome back, {user.full_name}!
              </h2>

              <p className="max-w-xl leading-relaxed text-on-surface-variant">
                Manage your academic journey from one central workspace. Here
                you can browse your active enrollments, view your assessments,
                and prepare for upcoming evaluations.
              </p>
            </div>

            <div className="absolute -bottom-16 -right-16 h-64 w-64 rounded-full bg-primary-container/30 blur-3xl"></div>
          </div>

          <div className="flex flex-col justify-center gap-6 rounded-xl bg-surface-container p-8 lg:col-span-4">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                Search Curriculum
              </label>

              <SearchCouse
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCouses.map((course, index) => (
            <CourseCard
              key={course.id}
              courseId={course.id}
              courseCode={course.course_code}
              courseName={course.course_name}
              description={course.description}
              index={index}
            />
          ))}
        </div>
      </div>
    </main>
  );
}
