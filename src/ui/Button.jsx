import styled, { css } from "styled-components";

const ButtonTypes = {
  submit: css`
    background: var(--color-tertiary);
  `,
};

const Button = styled.button`
  border: 0;
  border-radius: 10px;
  padding: var(--space-m) var(--space-2xl);
  font-weight: 700;
  cursor: pointer;
  color: var(--color-light);
  background: var(--color-secondary);

  ${({ $variant }) => ButtonTypes[$variant]}
`;

export default Button;
