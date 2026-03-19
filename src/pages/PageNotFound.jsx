import { Link } from "react-router";
import styled from "styled-components";

const StyledPageNotFound = styled.div`
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: var(--color-primary-tint);
`;

const PageNotFoundCard = styled.div`
  display: flex;
  flex-direction: column;
  width: 50%;
  max-width: 75ch;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 16px;
  padding: var(--space-5xl) var(--space-4xl);
  gap: var(--space-xl);
`;

const Title = styled.h1`
  color: var(--color-primary);
`;

const Text = styled.p`
  color: var(--color-dark-2);
  line-height: 1.5;
`;

const ActionsContainer = styled.div`
  display: flex;
  gap: var(--space-l);
  margin-top: var(--space-m);
`;

const ButtonLink = styled(Link)`
  text-decoration: none;
  border-radius: 12px;
  padding: var(--space-l) var(--space-2xl);
  font-weight: 700;
  border: 1px solid rgba(var(--color-primary-rgb), 0.18);
  color: var(--color-primary);

  background: ${({ $variant }) =>
    $variant === "primary" ? "var(--color-secondary)" : "transparent"};

  ${({ $variant }) =>
    $variant === "primary"
      ? "color: var(--color-light); border-color: transparent;"
      : ""}
`;

function PageNotFound() {
  return (
    <StyledPageNotFound>
      <PageNotFoundCard>
        <Title>404 - Page Not Found</Title>
        <Text>
          The page you’re looking for doesn’t exist. Use one of the options
          below to continue.
        </Text>

        <ActionsContainer>
          <ButtonLink to="/home" $variant="primary">
            Go to Home
          </ButtonLink>
          <ButtonLink to="/login">Go to Login</ButtonLink>
        </ActionsContainer>
      </PageNotFoundCard>
    </StyledPageNotFound>
  );
}

export default PageNotFound;
