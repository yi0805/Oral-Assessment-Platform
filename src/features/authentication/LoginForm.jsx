import { useNavigate } from "react-router";

function LoginForm({ role }) {
  const navigate = useNavigate();

  function handleFakeLogin() {
    navigate("/Home");
  }

  return (
    <div>
      <h1>{role} Login</h1>

      <input type="email" placeholder="Email" />
      <input type="password" placeholder="Password" />

      <button onClick={handleFakeLogin}>Log in</button>
    </div>
  );
}

export default LoginForm;
