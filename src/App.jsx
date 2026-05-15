import { BrowserRouter, Navigate, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "react-hot-toast";

import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import StudentGradedAssessment from "./features/student/StudentGradedAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import StudentCourse from "./features/student/StudentCourse";
import StudentAssessment from "./features/student/StudentAssessment";
import InstructorDashboard from "./features/instructor/InstructorDashboard";
import InstructorPendingGrades from "./features/instructor/InstructorPendingGrades";
import Transcript from "./features/instructor/Transcript";
import StudentManagement from "./features/instructor/StudentManagement";
import ProtectedLayout from "./ui/ProtectedRoute";
import Setting from "./features/instructor/Setting";
import AssessmentManagement from "./features/instructor/AssessmentManagement"
import InstructorCourseLayout from "./ui/InstructorCourseLayout";

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
                path="student/gradedAssessments"
                element={<StudentGradedAssessment />}
              />

              <Route
                path="instructor/pendingGrades"
                element={<InstructorPendingGrades />}
              />
              <Route
                path="instructor/transcript/:sessionId"
                element={<Transcript />}
              />
              <Route
                path="instructor/setting"
                element={<Setting />}
              />
              <Route path="instructor" element={<InstructorCourseLayout />}>
                <Route
                  path=":courseId"
                  element={<Navigate replace to="assessments" />}
                />
                <Route
                  path=":courseId/dashboard"
                  element={<InstructorDashboard />}
                />
                <Route
                  path=":courseId/users"
                  element={<StudentManagement />}
                />
                <Route
                  path=":courseId/assessments"
                  element={<AssessmentManagement />}
                />
              </Route>
            </Route>

            <Route
              path="student/:courseId/:assessmentConfigId"
              element={<StudentAssessment />}
            />
          </Route>

          <Route path="login" element={<Login />} />
          <Route path="*" element={<PageNotFound />} />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-center"
        gutter={12}
        containerStyle={{ margin: "8px" }}
        toastOptions={{
          style: {
            fontSize: "14px",
            maxWidth: "520px",
            padding: "14px 18px",
            borderRadius: "16px",
            background: "var(--color-surface-container-lowest)",
            color: "var(--color-on-surface)",
            border: "1px solid var(--color-outline-variant)",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.08)",
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: "var(--color-primary)",
              secondary: "var(--color-on-primary)",
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: "var(--color-error)",
              secondary: "var(--color-on-error)",
            },
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
