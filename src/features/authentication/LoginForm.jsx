import { useNavigate } from "react-router";
import styled from "styled-components";

const StyledLoginForm = styled.div`
  display: grid;
  place-items: center;
  padding: var(--space-5xl) var(--space-xl);
`;

const Title = styled.h1`
  font-size: var(--font-size-xxl);
  color: var(--color-primary);
  margin-bottom: var(--space-xl);
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: var(--space-l);
  width: 100%;
  max-width: 60ch;
  padding: var(--space-4xl);
  background: var(--color-light);
  border-radius: 14px;
  border: 1px solid var(--color-light-2);
`;

const Field = styled.label`
  display: block;
`;

const Input = styled.input`
  width: 100%;
  padding: var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  font-size: var(--font-size-default);

  &::placeholder {
    color: var(--color-dark-3-tint);
  }

  &:focus {
    border-color: var(--color-secondary);
  }
`;

const ActionsContainer = styled.div`
  width: 100%;
  margin-top: var(--space-m);
`;

const Button = styled.button`
  border: 0;
  border-radius: 10px;
  padding: var(--space-l) var(--space-2xl);
  background: ${({ $role }) =>
    $role === "student" ? "var(--color-secondary)" : "var(--color-tertiary)"};
  color: var(--color-light);
  font-weight: 700;
  cursor: pointer;
  width: 100%;
`;

function LoginForm({ role }) {
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    localStorage.setItem("role", role);
    navigate(`/home`);
  };

  return (
    <StyledLoginForm>
      <Title> Login</Title>

      <Form>
        <Field>
          <Input type="email" placeholder="Email" />
        </Field>

        <Field>
          <Input type="password" placeholder="Password" />
        </Field>

        <ActionsContainer>
          <Button type="submit" $role={role} onClick={handleLogin}>
            Log in
          </Button>
        </ActionsContainer>
      </Form>
    </StyledLoginForm>
  );
}

export default LoginForm;
