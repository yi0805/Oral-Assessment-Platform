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
      <Heading type="login">Select your role</Heading>

      <ActionsContainer type="login">
        <ButtonLink
          $variation="student"
          to="/home"
          onClick={() => handleChooseRole("student")}
        >
          Student
        </ButtonLink>

        <ButtonLink
          $variation="instructor"
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
