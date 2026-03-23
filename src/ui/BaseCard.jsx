import styled, { css } from "styled-components";

const cardTypes = {
  login: css`
    padding: var(--space-4xl);
    box-shadow: 0 10px 30px rgba(var(--color-primary-rgb), 0.12);
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
  border-radius: 16px;

  ${(props) => cardTypes[props.type]};
`;

export default BaseCard;
