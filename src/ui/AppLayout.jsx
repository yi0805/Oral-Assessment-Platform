import { Outlet } from "react-router";
import styled from "styled-components";

import Header from "./Header";
import Sidebar from "./Sidebar";

const StyleAppLayout = styled.div`
  display: grid;
  grid-template-columns: 16rem 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas: "header header" "sidebar main";
  height: 100vh;
  background: #2574ce21;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    grid-template-areas: "header" "sidebar" "main";
  }
`;

const Main = styled.main`
  grid-area: main;
  overflow: auto;
  padding: 10px var(--space-3xl);
  min-width: 0;
`;

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
