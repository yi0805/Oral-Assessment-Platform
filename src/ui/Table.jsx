import styled from "styled-components";

const TableWrapper = styled.div`
  width: 100%;
  max-width: 90ch;
  overflow-x: auto;
  margin-top: var(--space-xl);
`;

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    text-align: left;
    padding: var(--space-m) var(--space-l);
    border-bottom: 1px solid var(--color-light-2);
  }

  th {
    color: var(--color-primary);
    font-weight: 700;
    font-size: var(--font-size-s);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  tbody tr:hover {
    background: var(--color-primary-tint);
  }
`;

function Table({ children, ...props }) {
  return (
    <TableWrapper>
      <StyledTable {...props}>{children}</StyledTable>
    </TableWrapper>
  );
}

export default Table;
