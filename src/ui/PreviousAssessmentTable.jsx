import styled from "styled-components";

import Table from "./Table";
import Badge from "./Badge";

const ScoreText = styled.span`
  font-weight: 700;
  color: ${({ $pass }) =>
    $pass ? "var(--color-success)" : "var(--color-primary)"};
`;

function getStatusVariant(status) {
    {/*return green if AI's assessment grade is reviewed and published by the instructor */ }
  if (status === "Graded") return "success";
  return "info";
}

function PreviousAssessmentTable({ values }) {
  return (
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
        {values.map((row) => (
          <tr key={row.id}>
            <td>{row.course}</td>
            <td>{row.title}</td>
            <td>{row.date}</td>
            <td>
              <ScoreText $pass={row.score >= 60}>{row.score}</ScoreText>
            </td>
            <td>
              <Badge $variant={getStatusVariant(row.status)}>
                {row.status}
              </Badge>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default PreviousAssessmentTable;
