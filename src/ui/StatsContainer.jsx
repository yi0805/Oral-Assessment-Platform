import styled from "styled-components";

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: var(--space-xl);
  width: 90%;
  max-width: 100ch;
`;

export default StatsContainer;
