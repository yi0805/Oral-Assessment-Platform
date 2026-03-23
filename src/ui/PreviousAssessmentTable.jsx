import styled, { css } from "styled-components";

import Table from "./Table";

const scoreTypes = {
  pass: css`
    color: var(--color-success);
  `,
  fail: css`
    color: var(--color-primary);
  `,
};

const Score = styled.span`
  font-weight: 700;

  ${({ score }) => (score >= 60 ? scoreTypes.pass : scoreTypes.fail)}
`;

const statusTypes = {
  completed: css`
    background: rgba(var(--color-success-rgb), 0.12);
    color: var(--color-success);
  `,
  pending: css`
    background: var(--color-secondary-tint);
    color: var(--color-secondary);
  `,
};

const Status = styled.span`
  padding: var(--space-xs);
  border-radius: 999px;
  font-weight: 700;
  font-size: var(--font-size-s);

  ${({ status }) =>
    status === "Completed" ? statusTypes.completed : statusTypes.pending}
`;

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
              <Score score={row.score}>{row.score}</Score>
            </td>
            <td>
              <Status status={row.status}>{row.status}</Status>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default PreviousAssessmentTable;
