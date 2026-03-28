import useRequireAuth from "../hooks/useRequireAuth";

import StudentHome from "../features/student/StudentHome";
import InstructorHome from "../features/instructor/InstructorHome";

function Home() {
  const role = useRequireAuth();

  return role === "instructor" ? <InstructorHome /> : <StudentHome />;
}

export default Home;
