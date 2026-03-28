import { BrowserRouter, Navigate, Routes, Route } from "react-router";

import { GradebookProvider } from "./context/GradebookContext";
import GlobalStyle from "./styles/GlobalStyles";
import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import InstructorUpdateAssessment from "./pages/InstructorUpdateAssessment";
import PreviousAssessment from "./pages/PreviousAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import StudentCourse from "./features/student/StudentCourse";
import StudentAssessment from "./features/student/StudentAssessment";
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
                element={<PreviousAssessment />}
              />
              <Route
                path="instructor/update-assessment"
                element={<InstructorUpdateAssessment />}
              />
            </Route>

            <Route path="login" element={<Login />} />
            <Route path="*" element={<PageNotFound />} />

            <Route
              path="student/:courseId/:assessment"
              element={<StudentAssessment />}
            />
          </Routes>
        </BrowserRouter>
      </>
    </GradebookProvider>
  );
}

export default App;
