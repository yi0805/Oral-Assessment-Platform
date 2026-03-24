import Table from "./Table";

function InstructorTable({ values }) {
  return (
    <Table>
      <thead>
        <tr>
          <th>Student</th>
          <th>Score (out of 100)</th>
          <th>Time</th>
        </tr>
      </thead>

      <tbody>
        {values.map((r) => (
          <tr key={r.name}>
            <td>{r.name}</td>
            <td>{r.score}</td>
            <td>{r.time}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export default InstructorTable;
