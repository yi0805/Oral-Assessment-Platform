import { BrowserRouter, Navigate, Routes, Route } from "react-router";

import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import StudentPreviousAssessment from "./features/student/StudentPreviousAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import StudentCourse from "./features/student/StudentCourse";
import StudentAssessment from "./features/student/StudentAssessment";
import InstructorDashboard from "./features/instructor/InstructorDashboard";
import InstructorPendingGrades from "./features/instructor/InstructorPendingGrades";
import UpdateMaterial from "./features/instructor/UploadMaterial";
import Transcript from "./features/instructor/Transcript";

function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate replace to="/login" />} />

          <Route element={<AppLayout />}>
            <Route path="home" element={<Home />} />

            <Route path="student/:courseId" element={<StudentCourse />} />
            <Route
              path="student/previousAssessments"
              element={<StudentPreviousAssessment />}
            />

            <Route
              path="instructor/:courseId"
              element={<InstructorDashboard />}
            />
            <Route
              path="instructor/pendingGrades"
              element={<InstructorPendingGrades />}
            />
            <Route
              path="instructor/updateMaterial"
              element={<UpdateMaterial />}
            />
            <Route path="instructor/transcript" element={<Transcript />} />
          </Route>

          <Route path="login" element={<Login />} />
          <Route path="*" element={<PageNotFound />} />

          <Route
            path="student/:courseId/:assessmentId"
            element={<StudentAssessment />}
          />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
