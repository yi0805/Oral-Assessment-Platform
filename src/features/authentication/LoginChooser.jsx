import Stack from "../../ui/Stack";
import Heading from "../../ui/Heading";
import ActionsContainer from "../../ui/ActionsContainer";
import ButtonLink from "../../ui/ButtonLink";

function LoginChooser() {
  const handleChooseRole = (role) => {
    localStorage.setItem("role", role);
  };

  return (
    <Stack>
      <Heading $variant="centered">Select your role</Heading>

      <ActionsContainer $variant="centered">
        <ButtonLink
          $variant="primary"
          to="/home"
          onClick={() => handleChooseRole("student")}
        >
          Student
        </ButtonLink>

        <ButtonLink
          $variant="tertiary"
          to="/home"
          onClick={() => handleChooseRole("instructor")}
        >
          Instructor
        </ButtonLink>
      </ActionsContainer>
    </Stack>
  );
}

export default LoginChooser;
