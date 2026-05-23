import { Outlet } from "react-router";

import Header from "./Header";
import Sidebar from "./Sidebar";
import { useUser } from "../features/authentication/useUser";
import { useActiveCourseId } from "../hooks/useActiveCourseId";

function AppLayout() {
  const { user } = useUser();
  const activeCourseId = useActiveCourseId();

  const showSidebar =
    !!activeCourseId &&
    (user?.role === "student" || user?.role === "instructor");

  return (
    <>
      <Header />
      <div className="fixed top-16 z-40 h-[1px] w-full bg-[#eaeff1]"></div>

      {showSidebar && <Sidebar />}

      <div className={showSidebar ? "md:ml-64" : ""}>
        <Outlet />
      </div>
    </>
  );
}

export default AppLayout;
