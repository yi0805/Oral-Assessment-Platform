import { useNavigate } from "react-router";

function LoginChooser() {
  const navigate = useNavigate();

  return (
    <div>
      <h1>Select your role</h1>
      <button onClick={() => navigate("/login/student")}>Student</button>
      <button onClick={() => navigate("/login/instructor")}>Instructor</button>
    </div>
  );
}

export default LoginChooser;
