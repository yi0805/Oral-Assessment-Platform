import styled, { css } from "styled-components";

import { formControlFocus } from "./styles/shared";

const variants = {
  modal: css`
    width: 100%;
    max-width: 65ch;
    margin-top: var(--space-xl);
  `,
};

const Input = styled.input`
  padding: var(--space-m) var(--space-l);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-light-2);
  background: var(--color-light);

  ${formControlFocus}

  ${({ $variant }) => variants[$variant]}
`;

export default Input;
