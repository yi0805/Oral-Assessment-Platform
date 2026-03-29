import { BrowserRouter, Navigate, Routes, Route } from "react-router";

import { GradebookProvider } from "./context/GradebookContext";
import GlobalStyle from "./styles/GlobalStyles";
import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import InstructorUpdateAssessment from "./pages/InstructorUpdateAssessment";
import PreviousAssessment from "./pages/PreviousAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import StudentAssignments from "./features/student/StudentAssignments";
import StudentAssessment from "./features/student/StudentAssessment";
import UpdateMaterial from "./features/instructor/UploadMaterial";

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
              <Route
                path="student/previous-assessments"
                element={<PreviousAssessment />}
              />
              <Route
                path="instructor/update-assessment"
                element={<InstructorUpdateAssessment />}
              />
              <Route
                path="courses/:courseId/assignments"
                element={<StudentAssignments />}
              />
              <Route
                path="courses/:courseId/assessments/:assessmentId"
                element={<StudentAssessment />}
              />
              <Route
                path="instructor/update-material"
                element={<UpdateMaterial/>}
              />
            </Route>

            <Route path="login" element={<Login />} />

            <Route path="*" element={<PageNotFound />} />
          </Routes>
        </BrowserRouter>
      </>
    </GradebookProvider>
  );
}

export default App;
