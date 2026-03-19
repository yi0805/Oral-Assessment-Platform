import { useEffect } from "react";
import { useNavigate } from "react-router";
import styled from "styled-components";

import InstructorDashboard from "../features/dashboard/InstructorDashboard";
import StudentPractice from "../features/student/StudentPractice";

const StyledHome = styled.section`
  padding: var(--space-4xl);
`;

function Home() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  useEffect(() => {
    if (!role) navigate("/login");
  }, [navigate, role]);

  return (
    <StyledHome>
      {role === "instructor" ? <InstructorDashboard /> : <StudentPractice />}
    </StyledHome>
  );
}

export default Home;
