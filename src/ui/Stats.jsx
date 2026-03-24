import styled from "styled-components";

const StatCard = styled.div`
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-lg);
  padding: var(--space-3xl);
`;

const StatTitle = styled.p`
  color: var(--color-dark-1);
  margin-bottom: var(--space-s);
  font-size: var(--font-size-s);
`;

const StatValue = styled.p`
  color: var(--color-primary);
  font-size: var(--font-size-xxl);
  font-weight: 700;
`;

function Stats({ title, value }) {
  return (
    <StatCard>
      <StatTitle>{title}</StatTitle>
      <StatValue>{value}</StatValue>
    </StatCard>
  );
}

export default Stats;
