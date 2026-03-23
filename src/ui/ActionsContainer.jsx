import styled, { css } from "styled-components";

const ActionsContainerTypes = {
  login: css`
    justify-content: center;
    align-items: center;
  `,
};

const ActionsContainer = styled.div`
  display: flex;
  gap: var(--space-l);
  margin-top: var(--space-m);
  flex-wrap: wrap;

  ${(props) => ActionsContainerTypes[props.type]}
`;

export default ActionsContainer;
