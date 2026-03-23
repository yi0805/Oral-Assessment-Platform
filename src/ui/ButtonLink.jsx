import { Link } from "react-router";
import styled, { css } from "styled-components";

const variations = {
  primary: css`
    background: var(--color-secondary);
    color: var(--color-light);
    border-color: transparent;
  `,
  secondary: css`
    background: transparent;
  `,
  student: css`
    background: var(--color-secondary);
    color: var(--color-light);
    border-color: transparent;
  `,
  instructor: css`
    background: var(--color-tertiary);
    color: var(--color-light);
    border-color: transparent;
  `,
};

const ButtonLink = styled(Link)`
  text-decoration: none;
  border-radius: 12px;
  padding: var(--space-l) var(--space-2xl);
  font-weight: 700;
  border: 1px solid rgba(var(--color-primary-rgb), 0.18);
  color: var(--color-primary);
  cursor: pointer;

  ${(props) => variations[props.$variation]}
`;

export default ButtonLink;
