import styled, { css } from "styled-components";

const variants = {
  centered: css`
    justify-content: center;
    align-items: center;
  `,
  end: css`
    justify-content: flex-end;
    align-items: center;
  `,
};

const ActionsContainer = styled.div`
  display: flex;
  gap: var(--space-l);
  margin-top: var(--space-m);
  flex-wrap: wrap;

  ${({ $variant }) => variants[$variant]}
`;

export default ActionsContainer;
