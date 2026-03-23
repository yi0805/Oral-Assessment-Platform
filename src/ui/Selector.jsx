import styled from "styled-components";

const Select = styled.select`
  padding: var(--space-m) var(--space-l);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: var(--color-secondary);
    box-shadow: 0 0 0 2px var(--color-secondary-tint);
  }
`;

function Selector({ children, ...props }) {
  return <Select {...props}>{children}</Select>;
}

export default Selector;
