import styled, { css } from "styled-components";

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

  &:focus {
    outline: none;
    border-color: var(--color-secondary);
    box-shadow: 0 0 0 2px var(--color-secondary-tint);
  }

  ${({ $variant }) => variants[$variant]}
`;

export default Input;
