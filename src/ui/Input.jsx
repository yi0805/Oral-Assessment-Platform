import styled, { css } from "styled-components";

const inputTypes = {
  modal: css`
    width: 100%;
    max-width: 65ch;
    margin-top: var(--space-xl);
  `,
};

const Input = styled.input`
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  font-size: var(--font-size-default);

  ${({ $variant }) => inputTypes[$variant]}
`;

export default Input;
