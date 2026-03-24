import styled, { css } from "styled-components";

// For standalone card

const variants = {
  login: css`
    padding: var(--space-4xl);
    box-shadow: var(--shadow-md);
  `,
  notFound: css`
    display: flex;
    flex-direction: column;
    padding: var(--space-5xl) var(--space-4xl);
    gap: var(--space-xl);
  `,
};

const BaseCard = styled.div`
  width: 100%;
  max-width: 75ch;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-lg);

  ${({ $variant }) => variants[$variant]}
`;

export default BaseCard;
