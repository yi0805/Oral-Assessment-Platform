import { BrowserRouter, Navigate, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

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
import ProtectedLayout from "./ui/ProtectedRoute";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools initialIsOpen={false} />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate replace to="/login" />} />

          <Route element={<ProtectedLayout />}>
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
          </Route>

          <Route path="login" element={<Login />} />
          <Route path="*" element={<PageNotFound />} />

          <Route
            path="student/:courseId/:assessmentId"
            element={<StudentAssessment />}
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
