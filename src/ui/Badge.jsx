import styled, { css } from "styled-components";

const variants = {
  success: css`
    background: rgba(var(--color-success-rgb), 0.12);
    color: var(--color-success);
  `,
  info: css`
    background: var(--color-secondary-tint);
    color: var(--color-secondary);
  `,
  warning: css`
    background: rgba(var(--color-warning-rgb), 0.12);
    color: var(--color-dark-2);
  `,
  error: css`
    background: rgba(var(--color-error-rgb), 0.12);
    color: var(--color-error);
  `,
  neutral: css`
    background: var(--color-primary-tint);
    color: var(--color-primary);
  `,
};

const Badge = styled.span`
  display: inline-block;
  padding: var(--space-2xs) var(--space-s);
  border-radius: 999px;
  font-weight: 700;
  font-size: var(--font-size-s);

  ${({ $variant = "info" }) => variants[$variant]}
`;

export default Badge;
