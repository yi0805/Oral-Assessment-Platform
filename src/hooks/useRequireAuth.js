import { useEffect } from "react";
import { useNavigate } from "react-router";

function useRequireAuth() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  useEffect(() => {
    if (!role) navigate("/login");
  }, [navigate, role]);

  console.log("Here", role);
  return role;
}

export default useRequireAuth;
