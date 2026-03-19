import { useNavigate } from "react-router";
import { useMemo, useState } from "react";
import styled from "styled-components";

const Wrap = styled.div`
  display: grid;
  gap: var(--space-2xl);
`;

const Title = styled.h1`
  font-size: var(--font-size-xxl);
  color: var(--color-primary);
  text-transform: capitalize;
`;

const Form = styled.form`
  display: grid;
  gap: var(--space-l);
`;

const Field = styled.label`
  display: grid;
  gap: var(--space-xs);
`;

const Input = styled.input`
  width: 100%;
  padding: var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  font-size: var(--font-size-default);
  outline: none;

  &:focus {
    border-color: var(--color-secondary);
  }
`;

const ErrorBox = styled.div`
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-error);
  background: var(--color-light);
  color: var(--color-error);
  line-height: 1.4;
`;

const Actions = styled.div`
  display: flex;
  gap: var(--space-l);
  align-items: center;
  justify-content: flex-end;
`;

const Button = styled.button`
  appearance: none;
  border: 0;
  border-radius: 10px;
  padding: var(--space-l) var(--space-2xl);
  background: ${({ $role }) =>
    $role === "student" ? "var(--color-secondary)" : "var(--color-tertiary)"};
  color: var(--color-light);
  font-weight: 700;
  cursor: pointer;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
`;

function LoginForm({ role }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const roleLabel = useMemo(() => {
    if (role === "student") return "Student";
    if (role === "instructor") return "Instructor";
    return "User";
  }, [role]);

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const nextEmail = email.trim();
    const nextPassword = password;

    if (!nextEmail) {
      setError("Please enter your email.");
      return;
    }
    if (!nextPassword) {
      setError("Please enter your password.");
      return;
    }

    navigate(`/home?role=${encodeURIComponent(role || "")}`);
  }

  return (
    <Wrap>
      <div>
        <Title>{roleLabel} login</Title>
      </div>

      <Form onSubmit={handleSubmit}>
        <Field>
          <Input
            type="email"
            autoComplete="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Field>
          <Input
            type="password"
            autoComplete="current-password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>

        {error ? <ErrorBox role="alert">{error}</ErrorBox> : null}

        <Actions>
          <Button type="submit" $role={role}>
            Log in
          </Button>
        </Actions>
      </Form>
    </Wrap>
  );
}

export default LoginForm;
