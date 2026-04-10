import StudentHome from "../features/student/StudentHome";
import InstructorHome from "../features/instructor/InstructorHome";
import { useUser } from "../features/authentication/useUser";

function Home() {
  const { user } = useUser();

  return user?.role === "instructor" ? <InstructorHome /> : <StudentHome />;
}

export default Home;
