import styled from "styled-components";

const Table = styled.table`
  width: 100%;
  max-width: 90ch;
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

export default Table;
