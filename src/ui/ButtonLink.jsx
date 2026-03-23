import { Link } from "react-router";
import styled, { css } from "styled-components";

const variants = {
  primary: css`
    background: var(--color-secondary);
    color: var(--color-light);
    border-color: transparent;
  `,
  secondary: css`
    background: transparent;
    color: var(--color-primary);
    border-color: rgba(var(--color-primary-rgb), 0.18);

    &:hover {
      background: var(--color-secondary-tint);
    }
  `,
  tertiary: css`
    background: var(--color-tertiary);
    color: var(--color-light);
    border-color: transparent;
  `,
};

const ButtonLink = styled(Link)`
  display: inline-block;
  text-decoration: none;
  text-align: center;
  border-radius: var(--radius-md);
  padding: var(--space-l) var(--space-2xl);
  font-weight: 700;
  border: 1px solid transparent;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }

  &:focus-visible {
    outline: 2px solid var(--color-secondary);
    outline-offset: 2px;
  }

  ${({ $variant = "secondary" }) => variants[$variant]}
`;

export default ButtonLink;
