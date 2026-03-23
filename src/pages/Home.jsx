import styled from "styled-components";

import useRequireAuth from "../hooks/useRequireAuth";

import InstructorDashboard from "../features/dashboard/InstructorDashboard";
import StudentPractice from "../features/student/StudentPractice";

const StyledHome = styled.div`
  padding: var(--space-4xl);
`;

function Home() {
  const role = useRequireAuth();

  return (
    <StyledHome>
      {role === "instructor" ? <InstructorDashboard /> : <StudentPractice />}
    </StyledHome>
  );
}

export default Home;
