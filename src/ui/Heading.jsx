import styled, { css } from "styled-components";

const variants = {
  page: css`
    font-size: clamp(var(--font-size-xl), 4vw, var(--font-size-xxl));
  `,
  centered: css`
    text-align: center;
    font-size: clamp(var(--font-size-xl), 4vw, var(--font-size-xxl));
  `,
};

const Heading = styled.h1`
  color: var(--color-primary);
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-xl);
  overflow-wrap: break-word;

  ${({ $variant }) => variants[$variant]}
`;

export default Heading;
