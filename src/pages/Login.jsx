import LoginChooser from "../features/authentication/LoginChooser";
import styled from "styled-components";

const StyledLogin = styled.div`
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--space-4xl) var(--space-xl);
  background: var(--color-primary-tint);
`;

const Card = styled.div`
  width: 50%;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 16px;
  padding: var(--space-4xl);
  box-shadow: 0 10px 30px rgba(var(--color-primary-rgb), 0.12);
`;

function Login() {
  return (
    <StyledLogin>
      <Card>
        <LoginChooser />
      </Card>
    </StyledLogin>
  );
}

export default Login;
