import { BrowserRouter, Navigate, Routes, Route } from "react-router";

import GlobalStyle from "./styles/GlobalStyles";
import AppLayout from "./ui/AppLayout";
import Home from "./pages/Home";
import PreviousAssessment from "./pages/PreviousAssessment";
import PageNotFound from "./pages/PageNotFound";
import Login from "./pages/Login";
import LoginForm from "./features/authentication/LoginForm";

function App() {
  return (
    <>
      <GlobalStyle />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate replace to="/login" />} />

          <Route element={<AppLayout />}>
            <Route path="home" element={<Home />} />
            <Route
              path="previous-assessment"
              element={<PreviousAssessment />}
            />
          </Route>

          <Route path="login" element={<Login />} />
          <Route path="login/student" element={<LoginForm role="student" />} />
          <Route
            path="login/instructor"
            element={<LoginForm role="instructor" />}
          />

          <Route path="*" element={<PageNotFound />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
