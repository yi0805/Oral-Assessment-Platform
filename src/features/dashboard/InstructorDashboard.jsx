import { useMemo, useState } from "react";

import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import Selector from "../../ui/Selector";
import studentData from "../../data/studentData";
import courseOptions from "../../data/courseOption";
import InstructorTable from "../../ui/InstructorTable";

export default function InstructorDashboard() {
  const [courseNumber, setCourseNumber] = useState("");

  const overView = useMemo(() => studentData, []);

  return (
    <ContentCard>
      <Heading>Instructor dashboard</Heading>

      <Selector
        value={courseNumber}
        onChange={(e) => setCourseNumber(e.target.value)}
      >
        <option value="">Select the course number</option>
        {courseOptions.map((course) => (
          <option key={course.value} value={course.value}>
            {course.label}
          </option>
        ))}
      </Selector>

      {courseNumber ? <InstructorTable values={overView} /> : null}
    </ContentCard>
  );
}
