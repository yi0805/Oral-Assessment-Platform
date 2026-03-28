import useRequireAuth from "../../hooks/useRequireAuth";

import Stack from "../../ui/Stack";
import StatsContainer from "../../ui/StatsContainer";
import Stats from "../../ui/Stats";
import PreviousAssessmentScore from "../../data/previousAssessmentScore";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import PreviousAssessmentTable from "../../ui/PreviousAssessmentTable";
import FeedbackCard from "../../ui/FeedbackCard";
import ScoreBarChart from "../../ui/BarChart";
import getStudentByName from "../../utils/getStudentByname";
import getCoursesByStudent from "../../utils/getCoursesByStudent";
import CourseSelector from "../../ui/CourseSelector";
import { useState } from "react";

function StudentPreviousAssessment() {
  const userName = localStorage.getItem("userName");

  const student = getStudentByName(userName);
  const courses = student ? getCoursesByStudent(student) : [];

  const [selectedCourse, setSelectedCourse] = useState(courses[0]?.id || "");

  return (
    <div className="min-h-screen">
      <main className="px-8 pb-12 pt-24 md:ml-64">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10">
            <span className="text-xs font-medium uppercase tracking-widest text-outline">
              Performance History
            </span>
            <h1 className="mt-1 text-4xl font-extrabold tracking-tight text-on-surface">
              Previous Assessments
            </h1>

            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm font-semibold text-on-surface-variant">
                Course:
              </span>

              <CourseSelector
                courses={courses}
                selectedCourse={selectedCourse}
                onChange={setSelectedCourse}
              />
            </div>
          </div>
        </div>
      </main>
    </div>

    // useRequireAuth();

    // const totalAssessments = PreviousAssessmentScore.length;
    // const averageScore = Math.round(
    //   PreviousAssessmentScore.reduce((sum, row) => sum + row.score, 0) /
    //     PreviousAssessmentScore.length,
    // );
    // const bestScore = Math.max(
    //   ...PreviousAssessmentScore.map((row) => row.score),
    // );

    // <Stack>
    //   <StatsContainer>
    //     <Stats title="Total Assessments" value={totalAssessments} />
    //     <Stats title="Average Score" value={averageScore} />
    //     <Stats title="Best Score" value={bestScore} />
    //   </StatsContainer>

    //   <ContentCard>
    //     <Heading>Score Overview</Heading>
    //     <ScoreBarChart scores={PreviousAssessmentScore} />
    //   </ContentCard>

    //   <ContentCard>
    //     <Heading>Assessment history</Heading>

    //     <PreviousAssessmentTable values={PreviousAssessmentScore} />
    //   </ContentCard>

    //   <ContentCard>
    //     <Heading>Assessment feedback</Heading>

    //     <FeedbackCard title="Operating Systems" text="Impressive!" />

    //     <FeedbackCard
    //       title="Computer Organisation"
    //       text="Good job, but review linked lists."
    //     />
    //   </ContentCard>
    // </Stack>
  );
}

export default StudentPreviousAssessment;
