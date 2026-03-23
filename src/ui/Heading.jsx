import styled, { css } from "styled-components";

const headingTypes = {
  login: css`
    text-align: center;
    font-size: var(--font-size-xxl);
  `,
  student: css`
    font-size: var(--font-size-xxl);
  `,
};

const Heading = styled.h1`
  color: var(--color-primary);
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-xl);

  ${(props) => headingTypes[props.type]}
`;

export default Heading;
