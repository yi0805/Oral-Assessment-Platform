import { useMemo, useState } from "react";
import styled from "styled-components";

const StyledInstructorDashboard = styled.div`
  max-width: 56rem;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-4xl);
`;

const Title = styled.h1`
  margin-bottom: var(--space-xl);
`;

const Select = styled.select`
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  font-size: var(--font-size-default);
  background: var(--color-light);
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: var(--space-xl);

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

export default function InstructorDashboard() {
  const [courseNumber, setCourseNumber] = useState("");

  const instructorRows = useMemo(
    () => [
      { name: "Alice", score: 8, time: "Today" },
      { name: "Ben", score: 6, time: "Yesterday" },
      { name: "Chen", score: 9, time: "2 days ago" },
    ],
    [],
  );

  return (
    <StyledInstructorDashboard>
      <Title>Instructor dashboard</Title>

      <Select
        value={courseNumber}
        onChange={(e) => setCourseNumber(e.target.value)}
      >
        <option value="">Select the course number</option>
        <option value="CS101">CS110</option>
        <option value="CS102">CS210</option>
        <option value="CS201">CS340</option>
      </Select>

      {courseNumber ? (
        <Table>
          <tr>
            <th>Student</th>
            <th>Score (out of 100)</th>
            <th>Time</th>
          </tr>

          {instructorRows.map((r) => (
            <tr key={r.name}>
              <td>{r.name}</td>
              <td>{r.score}</td>
              <td>{r.time}</td>
            </tr>
          ))}
        </Table>
      ) : null}
    </StyledInstructorDashboard>
  );
}
