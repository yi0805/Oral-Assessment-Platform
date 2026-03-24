import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import styled from "styled-components";

const StyledPreviousAssessment = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-3xl);
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-xl);
  width: 90%;
  max-width: 72rem;
`;

const StatCard = styled.div`
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-3xl);
`;

const StatTitle = styled.p`
  color: var(--color-dark-1);
  margin-bottom: var(--space-s);
`;

const StatValue = styled.p`
  color: var(--color-primary);
  font-size: var(--font-size-xxl);
  font-weight: 700;
`;

const ContentCard = styled.div`
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-4xl);
  width: 90%;
  max-width: 72rem;
`;

const CourseTitle = styled.h2`
  color: var(--color-primary);
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-xl);
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    text-align: left;
    padding: var(--space-m);
    border-bottom: 1px solid var(--color-light-2);
    font-size: var(--font-size-default);
  }

  th {
    color: var(--color-primary);
  }
`;

const Score = styled.span`
  font-weight: 700;
  color: ${({ $score }) =>
    $score >= 60 ? "var(--color-success)" : "var(--color-primary)"};
`;

const Status = styled.span`
  padding: var(--space-xs);
  border-radius: 999px;
  background: ${({ $status }) =>
    $status === "Completed"
      ? "rgba(var(--color-success-rgb), 0.12)"
      : "var(--color-secondary-tint)"};
  color: ${({ $status }) =>
    $status === "Completed"
      ? "var(--color-success)"
      : "var(--color-secondary)"};
  font-weight: 700;
  font-size: var(--font-size-s);
`;

const FeedbackCard = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: 12px;
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
  background: var(--color-primary-tint);
`;

const FeedbackTitle = styled.h3`
  color: var(--color-primary);
  margin-bottom: var(--space-xs);
`;

const FeedbackText = styled.p`
  color: var(--color-dark-1);
  line-height: 1.5;
`;

function PreviousAssessment() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  useEffect(() => {
    if (!role) navigate("/login");
  }, [navigate, role]);

  const assessmentRows = useMemo(
    () => [
      {
        id: 1,
        course: "CS111",
        title: "An Introduction to Practical Computing",
        date: "18 Mar 2026",
        score: 20,
        status: "Completed",
      },
      {
        id: 2,
        course: "CS210",
        title: "Computer Organisation",
        date: "15 Mar 2026",
        score: 76,
        status: "Completed",
      },
      {
        id: 3,
        course: "CS340",
        title: "Operating Systems",
        date: "11 Mar 2026",
        score: 92,
        status: "Completed",
      },
      {
        id: 4,
        course: "CS110",
        title: "Introduction to Computer Systems",
        date: "08 Mar 2026",
        score: 81,
        status: "Reviewed",
      },
    ],
    [],
  );

  const totalAssessments = assessmentRows.length;
  const averageScore = Math.round(
    assessmentRows.reduce((sum, row) => sum + row.score, 0) /
      assessmentRows.length,
  );
  const bestScore = Math.max(...assessmentRows.map((row) => row.score));

  return (
    <StyledPreviousAssessment>
      <StatsContainer>
        <StatCard>
          <StatTitle>Total assessments</StatTitle>
          <StatValue>{totalAssessments}</StatValue>
        </StatCard>

        <StatCard>
          <StatTitle>Average score</StatTitle>
          <StatValue>{averageScore}%</StatValue>
        </StatCard>

        <StatCard>
          <StatTitle>Best score</StatTitle>
          <StatValue>{bestScore}%</StatValue>
        </StatCard>
      </StatsContainer>

      <ContentCard>
        <CourseTitle>Assessment history</CourseTitle>

        <Table>
          <thead>
            <tr>
              <th>Course</th>
              <th>Assessment</th>
              <th>Date</th>
              <th>Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {assessmentRows.map((row) => (
              <tr key={row.id}>
                <td>{row.course}</td>
                <td>{row.title}</td>
                <td>{row.date}</td>
                <td>
                  <Score $score={row.score}>{row.score}%</Score>
                </td>
                <td>
                  <Status $status={row.status}>{row.status}</Status>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </ContentCard>

      <ContentCard>
        <CourseTitle>Assessment feedback</CourseTitle>

        <FeedbackCard>
          <FeedbackTitle>Operating Systems</FeedbackTitle>
          <FeedbackText>Impressive!</FeedbackText>
        </FeedbackCard>

        <FeedbackCard>
          <FeedbackTitle>Computer Organisation</FeedbackTitle>
          <FeedbackText>Good understanding</FeedbackText>
        </FeedbackCard>
      </ContentCard>
    </StyledPreviousAssessment>
  );
}

export default PreviousAssessment;
