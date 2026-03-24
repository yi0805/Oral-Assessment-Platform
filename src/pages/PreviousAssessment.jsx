import useRequireAuth from "../hooks/useRequireAuth";

import Stack from "../ui/Stack";
import StatsContainer from "../ui/StatsContainer";
import Stats from "../ui/Stats";
import PreviousAssessmentScore from "../data/previousAssessmentScore";
import ContentCard from "../ui/ContentCard";
import Heading from "../ui/Heading";
import PreviousAssessmentTable from "../ui/PreviousAssessmentTable";
import FeedbackCard from "../ui/FeedbackCard";

function PreviousAssessment() {
  useRequireAuth();

  const totalAssessments = PreviousAssessmentScore.length;
  const averageScore = Math.round(
    PreviousAssessmentScore.reduce((sum, row) => sum + row.score, 0) /
      PreviousAssessmentScore.length,
  );
  const bestScore = Math.max(
    ...PreviousAssessmentScore.map((row) => row.score),
  );

  return (
    <Stack>
      <StatsContainer>
        <Stats title="Total Assessments" value={totalAssessments} />
        <Stats title="Average Score" value={averageScore} />
        <Stats title="Best Score" value={bestScore} />
      </StatsContainer>

      <ContentCard>
        <Heading>Assessment history</Heading>

        <PreviousAssessmentTable values={PreviousAssessmentScore} />
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
