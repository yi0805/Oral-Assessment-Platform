import { useMemo } from "react";

import useRequireAuth from "../hooks/useRequireAuth";

import Stack from "../ui/Stack";
import StatsContainer from "../ui/StatsContainer";
import Stats from "../ui/Stats";
import PreviousAssessmentScore from "../data/PreviousassessmentScore";
import ContentCard from "../ui/ContentCard";
import Heading from "../ui/Heading";
import PreviousAssessmentTable from "../ui/PreviousAssessmentTable";
import FeedbackCard from "../ui/FeedbackCard";

function PreviousAssessment() {
  useRequireAuth();

  const assessmentRows = useMemo(() => PreviousAssessmentScore, []);

  const totalAssessments = assessmentRows.length;
  const averageScore = Math.round(
    assessmentRows.reduce((sum, row) => sum + row.score, 0) /
      assessmentRows.length,
  );
  const bestScore = Math.max(...assessmentRows.map((row) => row.score));

  return (
    <Stack>
      <StatsContainer>
        <Stats title="Total Assessments" value={totalAssessments} />
        <Stats title="Average Score" value={averageScore} />
        <Stats title="Best Score" value={bestScore} />
      </StatsContainer>

      <ContentCard>
        <Heading>Assessment history</Heading>

        <PreviousAssessmentTable values={assessmentRows} />
      </ContentCard>

      <ContentCard>
        <Heading>Assessment feedback</Heading>

        <FeedbackCard title="Operating Systems" text="Impressive!" />

        <FeedbackCard
          title="Computer Organisation"
          text="Good job, but review linked lists."
        />
      </ContentCard>
    </Stack>
  );
}

export default PreviousAssessment;
