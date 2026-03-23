import styled, { css } from "styled-components";

const variants = {
  page: css`
    font-size: var(--font-size-xxl);
  `,
  centered: css`
    text-align: center;
    font-size: var(--font-size-xxl);
  `,
};

const Heading = styled.h1`
  color: var(--color-primary);
  /* font-size: var(--font-size-xl); */
  margin-bottom: var(--space-xl);
  font-size: clamp(2rem, 6vw, var(--font-size-xxl));

  ${({ $variant }) => variants[$variant]}
`;

export default Heading;
