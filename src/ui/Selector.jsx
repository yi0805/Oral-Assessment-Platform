import styled from "styled-components";

import { formControlFocus } from "./styles/shared";

const Select = styled.select`
  display: block;
  width: 100%;
  max-width: 40ch;
  padding: var(--space-m) var(--space-l);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  cursor: pointer;

  ${formControlFocus}
`;

function Selector({ children, ...props }) {
  return <Select {...props}>{children}</Select>;
}

export default Selector;
