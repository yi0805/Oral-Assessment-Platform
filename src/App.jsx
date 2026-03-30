import { BrowserRouter, Navigate, Routes, Route } from "react-router";

import { GradebookProvider } from "./context/GradebookContext";
import GlobalStyle from "./styles/GlobalStyles";
import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import InstructorUpdateAssessment from "./pages/InstructorUpdateAssessment";
import StudentPreviousAssessment from "./features/student/StudentPreviousAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import StudentCourse from "./features/student/StudentCourse";
import StudentAssessment from "./features/student/StudentAssessment";
import InstructorDashboard from "./features/instructor/InstructorDashboard";
import InstructorPendingGrades from "./features/instructor/InstructorPendingGrades";
import UpdateMaterial from "./features/instructor/UploadMaterial";
import Transcript from "./features/instructor/Transcript";
import AddCourse from "./features/instructor/AddCourse";
import InstructorCourseDashboard from "./features/instructor/InstructorCourseDashboard";

function App() {
  return (
    <GradebookProvider>
      <>
        <GlobalStyle />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate replace to="/login" />} />

            <Route element={<AppLayout />}>
              <Route path="home" element={<Home />} />

              <Route path="student/:courseId" element={<StudentCourse />} />
              <Route
                path="student/previous-assessments"
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
                path="instructor/update-assessment"
                element={<InstructorUpdateAssessment />}
              />
              <Route
                path="instructor/update-material"
                element={<UpdateMaterial/>}
              />
              <Route
                path="instructor/transcript"
                element={<Transcript/>}
              />
              <Route
                path="instructor/AddCourse"
                element={<AddCourse/>}
              />
              <Route
                path="instructor/course-dashboard"
                element={<InstructorCourseDashboard/>}
              />
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
    </GradebookProvider>
  );
}

export default App;
