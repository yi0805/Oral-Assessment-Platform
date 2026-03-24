import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useGoogleOAuth } from "@react-oauth/google";

import Stack from "../../ui/Stack";
import Heading from "../../ui/Heading";
import ActionsContainer from "../../ui/ActionsContainer";
import Button from "../../ui/Button";

const REDIRECT_URI = `${window.location.origin}/login`;

function LoginChooser() {
  const navigate = useNavigate();
  const { clientId } = useGoogleOAuth();

  useEffect(() => {
    const hash = window.location.hash.substring(1);
    if (!hash) return;

    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    if (!accessToken) return;

    window.history.replaceState({}, document.title, window.location.pathname);

    async function handleRedirectResponse() {
      try {
        const res = await fetch(
          "https://www.googleapis.com/oauth2/v3/userinfo",
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          },
        );

        if (!res.ok) throw new Error("Failed to fetch user info");

        const userInfo = await res.json();
        localStorage.setItem("userName", userInfo.name);
        localStorage.setItem("userPicture", userInfo.picture);

        navigate("/home");
      } catch (err) {
        console.error("Fetch user info error:", err);
      }
    }

    handleRedirectResponse();
  }, [navigate]);

  const handleChooseRole = (role) => {
    localStorage.setItem("role", role);

    const authParams = new URLSearchParams({
      client_id: clientId,
      redirect_uri: REDIRECT_URI,
      response_type: "token",
      scope: "openid profile email",
      include_granted_scopes: "true",
      prompt: "select_account",
    });

    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${authParams}`;
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
