import { Navigate, Outlet } from "react-router";
import { useUser } from "../features/authentication/useUser";
import Loading from "./Loading";

function ProtectedLayout() {
  const { isLoading, isError, user } = useUser();

  if (isLoading) return <Loading />;

  if (isError || !user) return <Navigate to="/login" replace />;

  return <Outlet />;
}

export default ProtectedLayout;
