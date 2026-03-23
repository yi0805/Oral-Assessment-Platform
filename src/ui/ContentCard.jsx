import styled, { css } from "styled-components";

const variants = {
  modal: css`
    max-width: 65ch;
  `,
};

const ContentCard = styled.div`
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-lg);
  padding: var(--space-4xl);
  width: 100%;
  max-width: 120ch;

  ${({ $variant }) => variants[$variant]}
`;

export default ContentCard;
