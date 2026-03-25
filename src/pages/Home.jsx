import useRequireAuth from "../hooks/useRequireAuth";

import InstructorDashboard from "../features/dashboard/InstructorDashboard";
import StudentHome from "../features/student/StudentHome";
import InstructorHome from "../features/dashboard/InstructorHome";

function Home() {
  const role = useRequireAuth();

  return role === "instructor" ? <InstructorHome /> : <StudentHome />;
}

export default Home;
