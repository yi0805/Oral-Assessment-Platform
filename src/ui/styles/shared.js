import { css } from "styled-components";

export const focusRing = css`
  &:focus-visible {
    outline: 2px solid var(--color-secondary);
    outline-offset: 2px;
  }
`;

export const formControlFocus = css`
  &:focus {
    outline: none;
    border-color: var(--color-secondary);
    box-shadow: 0 0 0 2px var(--color-secondary-tint);
  }
`;
