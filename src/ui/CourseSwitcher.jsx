import { useMatch, useNavigate } from "react-router";

import { useCourses } from "../hooks/useCourses";
import CourseSelector from "./CourseSelector";

export default function CourseSwitcher() {
  const match = useMatch("/instructor/:courseId/*");
  const navigate = useNavigate();
  const { courses } = useCourses();

  if (!match || courses.length === 0) return null;

  const subpath = match.params["*"] || "dashboard";

  return (
    <div className="mb-4 px-6">
      <CourseSelector
        courses={courses}
        selectedCourse={match.params.courseId}
        onChange={(nextId) => navigate(`/instructor/${nextId}/${subpath}`)}
      />
    </div>
  );
}
