import { useRef } from "react";
import { useNavigate } from "react-router";
import { useGoogleLogin } from "@react-oauth/google";

import Stack from "../../ui/Stack";
import Heading from "../../ui/Heading";
import ActionsContainer from "../../ui/ActionsContainer";
import Button from "../../ui/Button";

function LoginChooser() {
  const navigate = useNavigate();
  const pendingRole = useRef(null);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const res = await fetch(
          "https://www.googleapis.com/oauth2/v3/userinfo",
          {
            headers: {
              Authorization: `Bearer ${tokenResponse.access_token}`,
            },
          },
        );

        if (!res.ok) throw new Error("Failed to fetch user info");

        const userInfo = await res.json();
        localStorage.setItem("role", pendingRole.current);
        localStorage.setItem("userName", userInfo.name);
        localStorage.setItem("userPicture", userInfo.picture);
        navigate("/home");
      } catch (err) {
        console.error("Login error:", err);
      }
    },
    onError: (error) => console.log("Google login failed:", error),
  });

  const handleChooseRole = (role) => {
    pendingRole.current = role;
    googleLogin();
  };

  return (
    <Stack>
      <Heading $variant="centered">Select your role</Heading>

      <ActionsContainer $variant="centered">
        <Button $variant="primary" onClick={() => handleChooseRole("student")}>
          Student
        </Button>

        <Button
          $variant="tertiary"
          onClick={() => handleChooseRole("instructor")}
        >
          Instructor
        </Button>
      </ActionsContainer>
    </Stack>
  );
}

export default LoginChooser;
