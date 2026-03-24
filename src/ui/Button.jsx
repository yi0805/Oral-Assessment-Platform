import styled, { css } from "styled-components";

import { focusRing } from "./styles/shared";

const variants = {
  primary: css`
    background: var(--color-secondary);
    color: var(--color-light);
    border-color: transparent;
  `,
  secondary: css`
    background: transparent;
    color: var(--color-secondary);
    border-color: var(--color-secondary);

    &:hover:not(:disabled) {
      background: var(--color-secondary-tint);
    }
  `,
  tertiary: css`
    background: var(--color-tertiary);
    color: var(--color-light);
    border-color: transparent;
  `,
};

const Button = styled.button`
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: var(--space-m) var(--space-2xl);
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);

  &:hover:not(:disabled) {
    opacity: 0.9;
  }

  ${focusRing}

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  ${({ $variant = "primary" }) => variants[$variant]}
`;

export default Button;
