import { Outlet } from "react-router";

import Header from "./Header";
import Sidebar from "./Sidebar";

function AppLayout() {
  return (
    <>
      <Header />
      <div className="fixed top-16 z-40 h-[1px] w-full bg-[#eaeff1]"></div>
      <Sidebar />
      <Outlet />
    </>
  );
}

export default AppLayout;
