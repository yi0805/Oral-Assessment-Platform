import CourseCard from "./CourseCard";

function CourseGrid({ courses }) {
  return (
    <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
      {courses.map((course, index) => (
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
  );
}

export default CourseGrid;
