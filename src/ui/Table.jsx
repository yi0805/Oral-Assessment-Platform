import styled from "styled-components";

const Table = styled.table`
  width: 100%;
  max-width: 90ch;
  border-collapse: collapse;
  margin-top: var(--space-xl);

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

export default Table;
