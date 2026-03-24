import styled from "styled-components";
import BodyText from "./BodyText";

const Card = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  background: var(--color-primary-tint);

  & + & {
    margin-top: var(--space-l);
  }
`;

const Title = styled.h3`
  color: var(--color-primary);
  margin-bottom: var(--space-xs);
`;

function FeedbackCard({ title, text }) {
  return (
    <Card>
      <Title>{title}</Title>
      <BodyText>{text}</BodyText>
    </Card>
  );
}

export default FeedbackCard;
