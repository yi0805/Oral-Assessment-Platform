import styled, { css } from "styled-components";

const ContentCardType = {
  model: css`
    max-width: 65ch;
  `,
};

const ContentCard = styled.div`
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-4xl);
  width: 100%;
  max-width: 120ch;

  ${(props) => ContentCardType[props.type]}
`;

export default ContentCard;
