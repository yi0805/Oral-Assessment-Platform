import useRequireAuth from "../hooks/useRequireAuth";

import InstructorDashboard from "../features/dashboard/InstructorDashboard";
import StudentHome from "../features/student/StudentHome";

function Home() {
  const role = useRequireAuth();

  return role === "instructor" ? <InstructorDashboard /> : <StudentHome />;
}

export default Home;
