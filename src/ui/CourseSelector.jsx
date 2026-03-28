function CourseSelector({ courses, selectedCourse, onChange }) {
  console.log(courses);
  return (
    <div className="relative flex max-w-xs items-center">
      <select
        className="w-full cursor-pointer appearance-none rounded-lg border border-outline-variant/30 bg-surface-container-lowest py-2.5 pl-4 pr-10 text-sm font-semibold text-on-surface transition-colors hover:border-outline focus:outline-none focus:ring-1 focus:ring-primary/20"
        value={selectedCourse}
        onChange={(e) => onChange(e.target.value)}
      >
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.id} : {course.name}
          </option>
        ))}
      </select>
      <span className="material-symbols-outlined pointer-events-none absolute right-3 text-on-surface-variant">
        expand_more
      </span>
    </div>
  );
}

export default CourseSelector;
