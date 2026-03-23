import useRequireAuth from "../hooks/useRequireAuth";

import InstructorDashboard from "../features/dashboard/InstructorDashboard";
import StudentPractice from "../features/student/StudentPractice";

function Home() {
  const role = useRequireAuth();

  return role === "instructor" ? <InstructorDashboard /> : <StudentPractice />;
}

export default Home;
