import styled from "styled-components";

const Select = styled.select`
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  font-size: var(--font-size-default);
  background: var(--color-light);
`;

function Selector({ value, onChange, children }) {
  return (
    <Select value={value} onChange={onChange}>
      {children}
    </Select>
  );
}

export default Selector;
