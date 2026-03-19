import { useNavigate } from "react-router";
import styled from "styled-components";

const StyledLoginChooser = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
`;

const Title = styled.h1`
  text-align: center;
  font-size: var(--font-size-xxl);
  color: var(--color-primary);
`;

const Actions = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-l);
  margin-top: var(--space-m);
`;

const Button = styled.button`
  border: 0;
  border-radius: 12px;
  padding: var(--space-l) var(--space-2xl);
  font-weight: 700;
  cursor: pointer;
  color: var(--color-light);
  background: ${({ $variant }) =>
    $variant === "student"
      ? "var(--color-secondary)"
      : "var(--color-tertiary)"};
`;

function LoginChooser() {
  const navigate = useNavigate();

  return (
    <StyledLoginChooser>
      <Title>Select your role</Title>

      <Actions>
        <Button
          type="button"
          $variant="student"
          onClick={() => navigate("/login/student")}
        >
          Student
        </Button>

        <Button
          type="button"
          $variant="instructor"
          onClick={() => navigate("/login/instructor")}
        >
          Instructor
        </Button>
      </Actions>
    </StyledLoginChooser>
  );
}

export default LoginChooser;
