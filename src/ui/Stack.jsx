import styled from "styled-components";

const Stack = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${({ $gap }) => $gap || "var(--space-3xl)"};
  align-items: ${({ $align }) => $align || "center"};
`;

export default Stack;
