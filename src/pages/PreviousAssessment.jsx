import useRequireAuth from "../hooks/useRequireAuth";

import Stack from "../ui/Stack";
import StatsContainer from "../ui/StatsContainer";
import Stats from "../ui/Stats";
import PreviousAssessmentScore from "../data/previousAssessmentScore";
import ContentCard from "../ui/ContentCard";
import Heading from "../ui/Heading";
import PreviousAssessmentTable from "../ui/PreviousAssessmentTable";
import FeedbackCard from "../ui/FeedbackCard";
import ScoreBarChart from "../ui/BarChart";

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

    {/*create data for the chart*/ }
    const gradeCounts = { A: 0, B: 0, C: 0, D: 0 };

    PreviousAssessmentScore.forEach((item) => {
        const score = item.score;

        if (score >= 80) gradeCounts.A++;
        else if (score >= 70) gradeCounts.B++;
        else if (score >= 60) gradeCounts.C++;
        else gradeCounts.D++;
    });

    const chartData = [
        { name: "A", students: gradeCounts.A },
        { name: "B", students: gradeCounts.B },
        { name: "C", students: gradeCounts.C },
        { name: "D", students: gradeCounts.D },
    ];

    return (
    <Stack>
      <StatsContainer>
        <Stats title="Total Assessments" value={totalAssessments} />
        <Stats title="Average Score" value={averageScore} />
        <Stats title="Best Score" value={bestScore} />
       </StatsContainer>

     <ContentCard>
           <Heading>Score Overview</Heading>
           <ScoreBarChart data={chartData} />
     </ContentCard>

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
