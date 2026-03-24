import LoginChooser from "../features/authentication/LoginChooser";
import BaseCard from "../ui/BaseCard";
import StandaloneLayout from "../ui/StandaloneLayout";

function Login() {
  return (
    <StandaloneLayout>
      <BaseCard $variant="login">
        <LoginChooser />
      </BaseCard>
    </StandaloneLayout>
  );
}

export default Login;
